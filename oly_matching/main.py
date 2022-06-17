import logging

import pandas as pd

from oly_matching import constants as c
from oly_matching import clean, extract, match, analyze, pretty_logging

pretty_logging.configure_logger(logging.INFO)


def main(
    lis_path: str = "/Users/lennartdamen/Documents/code/olyslager/data/raw/lis.xlsx",
    tecdoc_path: str = "/Users/lennartdamen/Documents/code/olyslager/data/raw/tecdoc.xlsx",
    output_folder: str = "/Users/lennartdamen/Documents/code/olyslager/data/output",
):
    """Main script. Loads, cleans, matches, and analyzes lis and tecdoc data

    Args:
        lis_path: path to LIS excel file
        tecdoc_path: path to TecDoc excel file
    """
    logging.info("Loading TecDoc records...")
    df_tecdoc = pd.read_excel(
        io=tecdoc_path,
        parse_dates=[7, 8]
    )
    logging.info("Loading TecDoc complete.")
    logging.info("Loading LIS records...")
    df_lis = pd.read_excel(lis_path)
    logging.info("Loading LIS complete.")

    logging.info(f"Tecdoc: {df_tecdoc.shape}")
    logging.info(f"Lis: {df_lis.shape}")

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

    # Extract important LIS information and append as columns
    df_lis = extract.extract_and_append_relevant_data_lis(df_lis)

    # Clean the columns from LIS and TecDoc so that they have the same format
    df_lis = clean.clean_lis(df_lis)
    df_tecdoc = clean.clean_tecdoc(df_tecdoc)

    # Matching
    # If essential columns are missing, delete the record
    ix_keep = df_tecdoc[c.REQUIRED_MATCHING_COLS].notnull().all(axis=1)
    df_tecdoc = df_tecdoc[ix_keep]
    df_tecdoc["in_tecdoc"] = True

    ix_keep = df_lis[c.REQUIRED_MATCHING_COLS].notnull().all(axis=1)
    df_lis = df_lis[ix_keep]

    df_lis = df_lis.reset_index(drop=True)
    df_tecdoc = df_tecdoc.reset_index(drop=True)

    # TODO: current matching designed specifically to deal with mercedes-benz
    #  because of wildcard in engine code. Deal with other makes in future too.
    is_mercedes_record = df_lis["make"] == "mercedesbenz"
    df_lis_mercedes = df_lis[is_mercedes_record]
    # df_rest = df_lis[~is_mercedes_record]

    df_lis_matched = match.match_mercedes(df_lis_mercedes, df_tecdoc)
    df_lis_matched.to_csv(f"{output_folder}/lis_records_with_match.csv", index=False)

    lis_id_with_n_types = analyze.get_lis_id_with_n_types(df_lis_matched)
    lis_id_with_n_types.to_csv(f"{output_folder}/lis_ids_with_n_types.csv")

    unique_lis_types = df_lis_original["type_id"].unique()
    unmatched_lis_ids = [x for x in unique_lis_types if x not in lis_id_with_n_types.index]
    pd.Series(unmatched_lis_ids).to_csv(f"{output_folder}/unmatched_lis_ds.csv", index=False)

    logging.info(
        f"Perentage matched = {len(lis_id_with_n_types)}/{len(unique_lis_types)} = "
        f"{len(lis_id_with_n_types)/len(unique_lis_types) * 100}%"
    )


if __name__ == "__main__":
    main()

# What % of matches can we expect if the engine code is NOT missing?
# engine_codes = clean.extract_mercedes_engine_code(df_lis_original["component_code"])
# ix_keep = engine_codes.notnull()
# lis_types_with_engine_code = df_lis_original.loc[ix_keep, "type_id"].unique()
# has_engine_code = np.isin(df_matched["type_id"], lis_types_with_engine_code)
# lis_id_with_n_types = df_matched[has_engine_code].groupby("type_id").apply(lambda x: x["N-Type No."].unique())
# logging.info(
#     "For all LIS types that have an engine code, "
#     f"{len(lis_id_with_n_types)}/{len(lis_types_with_engine_code)} "
#     f"={len(lis_id_with_n_types)/len(lis_types_with_engine_code)*100}% get one or more N-types"
# )

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
