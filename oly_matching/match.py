import logging
import pandas as pd

MATCHING_MERGE_COLS = ["make", "model", "type", "category", "component_code_clean"]


def match_tecdoc_records_to_lis(df_lis: pd.DataFrame, df_tecdoc: pd.DataFrame) -> pd.DataFrame:
    """Tries to match every record from lis against a record from tecdoc (left join)

    Assumes df_lis and df_tecdoc are already clean!
    """
    logging.info("Starting matching process...")
    df_lis_matched = match_on_required_columns(df_lis, df_tecdoc)
    df_lis_matched = keep_records_start_year_close(df_lis_matched)
    df_lis_matched = keep_records_with_matching_axle_config(df_lis_matched)
    df_lis_matched["in_tecdoc"] = df_lis_matched["in_tecdoc"].replace(to_replace=[None], value=False)
    logging.info("Matching completed successfully.")
    return df_lis_matched


def match_on_required_columns(df_lis: pd.DataFrame, df_tecdoc: pd.DataFrame) -> pd.DataFrame:
    # Handling wildcards for Mercedes in LIS. Assumes TecDoc does NOT have any wildcards
    df_lis_loop = df_lis.copy(deep=True)
    df_tecdoc = df_tecdoc.copy(deep=True)

    df_lis_loop["component_code_clean"] = df_lis_loop["component_code"].copy(deep=True)
    df_tecdoc["component_code_clean"] = df_tecdoc["component_code"].copy(deep=True)

    df_matched_list = []
    while df_lis_loop.shape[0] != 0:
        row_ends_with_wildcard = df_lis_loop["component_code_clean"].str[-1] == "x"
        df_lis_i = df_lis_loop[~row_ends_with_wildcard]

        df_lis_matched = pd.merge(
            left=df_lis_i,
            right=df_tecdoc,
            how="left",
            on=MATCHING_MERGE_COLS,
            suffixes=("_lis", "_tecdoc")
        )
        df_matched_list.append(df_lis_matched)

        df_lis_loop = df_lis_loop.drop(index=df_lis_i.index)
        df_lis_loop["component_code_clean"] = df_lis_loop["component_code_clean"].str[:-1]
        df_tecdoc["component_code_clean"] = df_tecdoc["component_code_clean"].str[:-1]
    df_lis_matched = pd.concat(df_matched_list)
    df_lis_matched = df_lis_matched.drop(columns=["component_code_clean"])
    return df_lis_matched


def keep_records_start_year_close(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    diff_in_years = df[f"model_year_start_lis"] - df[f"model_year_start_tecdoc"]
    ix_keep = (diff_in_years.abs() <= 2) | (diff_in_years.isnull())
    logging.info(f"Dropping {len(df) - ix_keep.sum()} rows because model years to far apart")
    return df[ix_keep]


def keep_records_with_matching_axle_config(df: pd.DataFrame) -> pd.DataFrame:
    ix_keep = (
            df["axle_configuration_lis"].isnull()
            | (df["axle_configuration_lis"] == df["axle_configuration_tecdoc"])
    )
    logging.info(f"Dropping {ix_keep.sum()}/{df.shape[0]} records because axle config not matching")
    return df[ix_keep]
