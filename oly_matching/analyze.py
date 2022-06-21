import logging

import pandas as pd
import numpy as np

from oly_matching import clean


def get_lis_id_with_n_types(df_matched: pd.DataFrame) -> pd.DataFrame:
    df_matched = df_matched[df_matched["in_tecdoc"]]
    lis_id_with_n_types = (
        df_matched
        .groupby("type_id")
        .apply(lambda x: x["N-Type No."].unique())
    )
    return lis_id_with_n_types


def percentage_matched_if_engine_code_present(df_lis_original: pd.DataFrame, df_lis_matched: pd.DataFrame) -> float:
    # What % of matches can we expect if the engine code is NOT missing?
    df_lis_original = df_lis_original.copy(deep=True)
    df_lis_original = clean.clean_string_columns(df_lis_original)
    df_lis_original = clean.clean_engine_code(df_lis_original)
    has_engine_code = df_lis_original.groupby("type_id").apply(lambda x: x["component_code"].notnull().any())
    lis_types_with_engine_code = has_engine_code[has_engine_code].index
    has_engine_code = np.isin(df_lis_matched["type_id"], lis_types_with_engine_code)
    df_lis_matched_with_engine_code = df_lis_matched[has_engine_code]
    lis_id_with_n_types = get_lis_id_with_n_types(df_lis_matched_with_engine_code)
    percentage_matched = len(lis_id_with_n_types) / len(lis_types_with_engine_code) * 100
    logging.info(
        "For all LIS types that have an engine code, "
        f"{len(lis_id_with_n_types)}/{len(lis_types_with_engine_code)} "
        f"={percentage_matched}% get one or more N-types"
    )
    return percentage_matched
