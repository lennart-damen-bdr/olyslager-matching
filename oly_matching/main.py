import logging

import pandas as pd

from oly_matching import constants as c
from oly_matching import clean, extract, match, analyze, pretty_logging

pretty_logging.configure_logger(logging.INFO)


def main(lis_path: str, tecdoc_path: str, output_folder: str, matching_method: str) -> None:
    """Main script. Loads, cleans, matches, and analyzes lis and tecdoc data

    Creates 4 files:
    - matches_per_lis_id.xlsx: for each LIS type ID, state which N-types correspond to it (together with extra info)
    - metrics: overall overview of matching performance
    - results_per_model.xlsx: overview of performance per model (useful for identifying algorithm improvements)
    - lis_records_with_match.xlsx: detailed records from LIS, left-joined with corresponding TecDoc records

    Args:
        lis_path: path to LIS excel file
        tecdoc_path: path to TecDoc excel file
        output_folder: where to store the output files
        matching_method: 'exact', 'cut_strings', 'fuzzy'
    """
    logging.info("Loading TecDoc records...")
    # df_tecdoc = pd.read_excel(
    #     io=tecdoc_path,
    #     parse_dates=[7, 8]
    # )
    df_tecdoc = pd.read_pickle("./data/raw/tecdoc.pkl")
    logging.info(f"Loading TecDoc complete. Shape: {df_tecdoc.shape}")

    logging.info("Loading LIS records...")
    # df_lis = pd.read_excel(lis_path)
    df_lis = pd.read_pickle("./data/raw/lis.pkl")
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
    df_lis_matched = match.match_tecdoc_records_to_lis(df_lis, df_tecdoc, how=matching_method)

    # Saving output
    # All details about the matches
    df_links = analyze.get_links_and_original_data(df_lis_matched, df_lis_original, df_tecdoc_original)

    output_path = f"{output_folder}/links_with_original_data.xlsx"
    df_links.to_excel(output_path, index=False)
    logging.info(f"Saved links between LIS and N-type together with original LIS and TecDoc data to {output_path}.")

    # Results per LIS ID
    df_lis_original = clean.clean_string_columns(df_lis_original)
    df_lis_original = clean.clean_engine_code(df_lis_original)
    df_lis_original = clean.clean_model_column_lis(df_lis_original)
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

    output_path = f"{output_folder}/matches_per_lis_id.xlsx"
    df_results.to_excel(output_path, index=False)
    logging.info(f"Saved list of LIS ID's with N-type to {output_path}.")

    # Results per model
    df_results_per_model = analyze.get_performance_per_model(df_results)
    output_path = f"{output_folder}/results_per_model.xlsx"
    df_results_per_model.to_excel(output_path, index=False)

    # Metrics
    n_matches = df_results["n_types"].notnull().sum()
    percentage_matched = n_matches / len(df_results) * 100
    logging.info(
        f"Percentage of LIS types that get at least one N-type = {n_matches}/{len(df_results)} = "
        f"{percentage_matched}%"
    )

    df_results_with_engine_code = df_results[df_results["has_engine_code"]]
    percentage_matched_with_engine_code = n_matches / len(df_results_with_engine_code) * 100
    logging.info(
        "For all LIS types that have an engine code, "
        f"{n_matches}/{len(df_results_with_engine_code)} "
        f"={percentage_matched_with_engine_code}% get one or more N-types"
    )

    metrics = pd.Series(
        data={
            "n_unique_lis_ids": len(df_results),
            "n_lis_ids_with_one_or_more_n_types": int(n_matches),
            "n_lis_ids_with_engine_code": len(df_results_with_engine_code),
            "percentage_matched": percentage_matched,
            "percentage_matched_with_engine_code": percentage_matched_with_engine_code
        },
        name="metrics",
    )
    output_path = f"{output_folder}/metrics.xlsx"
    metrics.to_excel(output_path)

    logging.info("Full matching process completed successfully.")
