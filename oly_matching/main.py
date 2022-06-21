import logging

import pandas as pd

from oly_matching import constants as c
from oly_matching import clean, extract, match, analyze, pretty_logging

pretty_logging.configure_logger(logging.INFO)


def main(lis_path: str, tecdoc_path: str, output_folder: str,) -> None:
    """Main script. Loads, cleans, matches, and analyzes lis and tecdoc data

    Creates 3 files:
    - lis_ids_with_n_types.csv: for each LIS type ID, state which N-types correspond to it
    - unmatched_lis_ids.csv: list of LIS ID's for which the algorithm could not find a match at all
    - lis_records_with_match.csv: detailed records from LIS, left-joined with corresponding TecDoc records

    Args:
        lis_path: path to LIS excel file
        tecdoc_path: path to TecDoc excel file
        output_folder: where to store the output files
    """
    logging.info("Loading TecDoc records...")
    df_tecdoc = pd.read_excel(
        io=tecdoc_path,
        parse_dates=[7, 8]
    )
    logging.info(f"Loading TecDoc complete. Shape: {df_tecdoc.shape}")

    logging.info("Loading LIS records...")
    df_lis = pd.read_excel(lis_path)
    logging.info(f"Loading LIS complete. Shape: {df_lis.shape}")

    # We keep only the LIS rows related to the engine
    df_lis = clean.keep_engine_records_lis(df_lis)

    # We only keep the columns we care about
    df_lis = df_lis[c.LIS_COLUMNS]
    df_tecdoc = df_tecdoc[c.TECDOC_COLUMNS]

    # Convert all time related columns to "year" as float
    df_tecdoc = clean.convert_time_cols_tecdoc(df=df_tecdoc)

    # Rename all tecdoc columns to correspond to LIS columns
    df_tecdoc = df_tecdoc.rename(columns=c.MATCHING_COLUMN_MAPPING)

    # Take one of the largest brands
    df_lis = clean.filter_records(df_lis)
    df_tecdoc = clean.filter_records(df_tecdoc)

    # Save the original data to compare matches later
    df_lis_original = df_lis.copy(deep=True)
    df_tecdoc_original = df_tecdoc.copy(deep=True)

    # Extract important LIS information and append as columns
    df_lis = extract.extract_and_append_relevant_data_lis(df_lis)

    # Clean the columns from LIS and TecDoc so that they have the same format
    df_lis = clean.clean_lis(df_lis)
    df_tecdoc = clean.clean_tecdoc(df_tecdoc)

    # Matching
    # If essential columns are missing, delete the record
    logging.info("Dropping rows from TecDoc that are missing critical matching data...")
    ix_keep = df_tecdoc[c.REQUIRED_MATCHING_COLS].notnull().all(axis=1)
    logging.info(f"Keeping {ix_keep.sum()}/{len(df_tecdoc)} rows")
    df_tecdoc = df_tecdoc[ix_keep]
    df_tecdoc["in_tecdoc"] = True

    logging.info("Dropping rows from LIS that are missing critical matching data...")
    ix_keep = df_lis[c.REQUIRED_MATCHING_COLS].notnull().all(axis=1)
    logging.info(f"Keeping {ix_keep.sum()}/{len(df_lis)} rows")
    df_lis = df_lis[ix_keep]

    df_lis = df_lis.reset_index(drop=True)
    df_tecdoc = df_tecdoc.reset_index(drop=True)

    # TODO: current matching designed specifically to deal with mercedes-benz
    #  because of wildcard in engine code. Deal with other makes in future too.
    # is_mercedes_record = df_lis["make"] == "mercedesbenz"
    # df_lis_mercedes = df_lis[is_mercedes_record]
    # df_rest = df_lis[~is_mercedes_record]

    # Saving output
    df_lis_matched = match.match_mercedes(df_lis, df_tecdoc)
    output_path = f"{output_folder}/lis_records_with_match.csv"
    df_lis_matched.to_csv(output_path, index=False)
    logging.info(f"Saved full LIS records with appended N-type to {output_path}.")

    lis_id_with_n_types = analyze.get_lis_id_with_n_types(df_lis_matched)
    output_path = f"{output_folder}/lis_ids_with_n_types.csv"
    lis_id_with_n_types.to_csv(output_path)
    logging.info(f"Saved list of LIS ID's with N-type to {output_path}.")

    unique_lis_types = df_lis_original["type_id"].unique()
    unmatched_lis_ids = pd.DataFrame(data=[x for x in unique_lis_types if x not in lis_id_with_n_types.index], columns=["type_id"])

    has_at_least_one_engine_code = df_lis.groupby("type_id").apply(lambda x: x["component_code"].notnull().any())
    has_at_least_one_engine_code = pd.DataFrame(has_at_least_one_engine_code, columns=["has_at_least_one_engine_code"])
    has_at_least_one_engine_code = has_at_least_one_engine_code.reset_index()
    unmatched_lis_ids = pd.merge(
        left=unmatched_lis_ids,
        right=has_at_least_one_engine_code,
        on=["type_id"],
        how="left",
    )
    unmatched_lis_ids["has_at_least_one_engine_code"] = unmatched_lis_ids["has_at_least_one_engine_code"].fillna(False)

    output_path = f"{output_folder}/unmatched_lis_ids.csv"
    unmatched_lis_ids.to_csv(output_path, index=False)
    logging.info(f"Saved list of LIS ID's that did not get an N-type to {output_path}.")

    percentage_matched = len(lis_id_with_n_types)/len(unique_lis_types) * 100
    logging.info(
        f"Percentage matched overall = {len(lis_id_with_n_types)}/{len(unique_lis_types)} = "
        f"{percentage_matched}%"
    )
    percentage_matched_with_engine_code = analyze.percentage_matched_if_engine_code_present(
        df_lis_original, df_lis_matched
    )
    logging.info("Full matching process completed successfully.")

# Mercedes-Benz
# - LIS
# --- make = Mercedes-Benz (COUNTRY)
# --- the country code is in capital between brackets
# --- model can contain 'Euro x' code, e.g. Atego Euro 5 (looks like always formatted with space)
# --- model can contain something like Construction/Chassis/tractor, like Actros II tractor Euro 6
# --- model is sometimes repeated in the type, but also often not (50-50?)
# --- type can contains L/LL/LS/K or jus LS
# --- type can contain the axle config, usually between brackets or sometimes separated by space
# --- type can also contain other info between brackets, such as (chassis), (tractor)
# --- component_code is formatted mostly like OMxxxLA, somtimes follow by a generation in Roman (IV)
# --- the component_code ALSO often contains Euro x after OMxxxLA.
#     Sometimes Euro x is in type, sometimes in component, sometimes both

# TecDoc
# --- make = MERCEDES-BENZ
# --- model = capitals, sometimes seperated by slash or space-slash-space
#             example: T2/L or ACTROS MP2 / MP3.
# --- model sometimes has an O NUMBER between brackets, like CONECTO () 345)
# --- In the vast majority, the model is NOT repeated in the type.
#     Ocassionally it IS repeated, like INTEGRO (0 550) - Integro
# --- component_code is formatted OM xxx.xxx in all cases I could see
# --- component_code my have info between brackets, like OM xxx.xxx (xx.xx-xx.xx)

# Plan
# --- only add new columns followed by suffix "_merge"
# --- extract and remove (COUNTRY) from LIS
# --- extract and remove Euro x from model and component_code from LIS
# --- extract and remove Construction/Chassis/tractor from model LIS
# --- remove model from the type column from LIS
# --- expand the slashes in the L/LL/LS/K (Tecdoc has xxxx AK or xxxxx S)
# --- for both, add a component_code column that looks like OMxxx (forgetting LA and more specific engine codes)

# MAN
# LIS
# - make can contain (BRA), but other than that fine
# - model can contain Euro code
# - type contains the model
# - type: after the model, there's digit(s).digits space LETTER(optional /LETTERS/...), e.g. 10.163 LLT/LLS
# - type can contain Euro code
# - type can contain SCR/EGR/...? /EEV?
# - type can contain the axle config (most records this is true)
# - type can be split by comma, e.g. TGX 26.420, 26,480, 26.500 (6x4 BB) Euro 6 --> what is BB?
# - type can be split by comma, e.g. TGS 35.430, 35.470, 35.510 BL,BB (8x4) (LK,TM) Euro 6d --> how to split this?
# - component_code almost always split by comma
# - component code can contain Euro code
# - component code can have different formats, e.g. 224 (D0826 LFL03 Euro 2), D 0826 LF 08, 313 (MAN D2866 LF26/EDC/Euro3)

# TecDoc
# - model TG(letter) I/II,
# - type theres digits.digits letters (sometimes comma letters, e.g. 26.460 DFLS, DFLRS)
# - component code looks like D 4-digits LETTER/DIGIT-code
# - component code can be separated by comma
