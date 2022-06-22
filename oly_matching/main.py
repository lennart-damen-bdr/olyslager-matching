import logging

import pandas as pd

from oly_matching import constants as c
from oly_matching import clean, extract, match, analyze, pretty_logging

pretty_logging.configure_logger(logging.INFO)


def main(lis_path: str, tecdoc_path: str, output_folder: str,) -> None:
    """Main script. Loads, cleans, matches, and analyzes lis and tecdoc data

    Creates 4 files:
    - matches_per_lis_id.csv: for each LIS type ID, state which N-types correspond to it (together with extra info)
    - metrics: overall overview of matching performance
    - results_per_model.csv: overview of performance per model (useful for identifying algorithm improvements)
    - lis_records_with_match.csv: detailed records from LIS, left-joined with corresponding TecDoc records

    Args:
        lis_path: path to LIS excel file
        tecdoc_path: path to TecDoc excel file
        output_folder: where to store the output files
    """
    logging.info("Loading TecDoc records...")
    # df_tecdoc = pd.read_excel(
    #     io=tecdoc_path,
    #     parse_dates=[7, 8]
    # )
    df_tecdoc = pd.read_pickle("/Users/lennartdamen/Documents/code/olyslager/data/raw/tecdoc.pkl")
    logging.info(f"Loading TecDoc complete. Shape: {df_tecdoc.shape}")

    logging.info("Loading LIS records...")
    # df_lis = pd.read_excel(lis_path)
    df_lis = pd.read_pickle("/Users/lennartdamen/Documents/code/olyslager/data/raw/lis.pkl")
    logging.info(f"Loading LIS complete. Shape: {df_lis.shape}")

    # We keep only the LIS rows related to the engine
    df_lis = clean.keep_engine_records_lis(df_lis)

    # We only keep the columns we care about
    df_lis = df_lis[c.LIS_COLUMNS]
    df_tecdoc = df_tecdoc[c.TECDOC_COLUMNS]

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

    # Matching
    df_lis_matched = match.match_tecdoc_records_to_lis(df_lis, df_tecdoc)

    # Saving output
    # All details about the matches
    output_path = f"{output_folder}/lis_records_with_match.csv"
    df_lis_matched.to_csv(output_path, index=False)
    logging.info(f"Saved full LIS records with appended N-type to {output_path}.")

    # Results per LIS ID
    df_lis_original = clean.clean_string_columns(df_lis_original)
    df_lis_original = clean.clean_engine_code(df_lis_original)
    df_lis_original["model"] = clean.clean_model_column_lis(df_lis_original["model"])
    df_lis_original["make"] = clean.clean_make_column(df_lis_original["make"])
    lis_id_has_engine_code = analyze.get_lis_id_has_engine_code(
        df=df_lis_original,
        id_col="type_id",
        engine_col="component_code"
    )
    df_results = pd.DataFrame(lis_id_has_engine_code)
    df_results["n_types"] = analyze.get_lis_id_with_n_types(df_lis_matched)
    for unique_property in ("make", "model"):
        df_results[unique_property] = analyze.get_unique_property_per_id(
            df=df_lis_original,
            id_col="type_id",
            property_col=unique_property
        )
    df_results["has_at_least_one_match"] = df_results["n_types"].notnull()
    df_results = df_results.reset_index()

    output_path = f"{output_folder}/matches_per_lis_id.csv"
    df_results.to_csv(output_path, index=False)
    logging.info(f"Saved list of LIS ID's with N-type to {output_path}.")

    # Results per model
    df_results_per_model = analyze.get_performance_per_model(df_results)
    output_path = f"{output_folder}/results_per_model.csv"
    df_results_per_model.to_csv(output_path, index=False)

    # Metrics
    n_matches = df_results["n_types"].notnull().sum()
    percentage_matched = n_matches / len(df_results) * 100
    logging.info(
        f"Percentage of LIS types that get at least one N-type = {n_matches}/{len(df_results)} = "
        f"{percentage_matched}%"
    )

    df_results_with_engine_code = df_results[df_results["has_engine_code"]]
    n_matches_with_engine_code = df_results_with_engine_code["n_types"].notnull().sum()
    percentage_matched_with_engine_code = n_matches_with_engine_code / len(df_results_with_engine_code) * 100
    logging.info(
        "For all LIS types that have an engine code, "
        f"{n_matches_with_engine_code}/{len(df_results_with_engine_code)} "
        f"={percentage_matched_with_engine_code}% get one or more N-types"
    )

    metrics = pd.Series(
        data={
            "n_unique_lis_ids": len(df_results),
            "n_lis_ids_with_one_or_more_n_types": int(n_matches),
            "n_lis_ids_with_engine_code": len(df_results_with_engine_code),
            "n_lis_ids_with_engine_code_with_one_or_more_n_types": int(n_matches_with_engine_code),
            "percentage_matched": percentage_matched,
            "percentage_matched_with_engine_code": percentage_matched_with_engine_code
        },
        name="metrics",
    )
    output_path = f"{output_folder}/metrics.csv"
    metrics.to_csv(output_path)

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
