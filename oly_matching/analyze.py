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
    engine_codes = clean.extract_mercedes_engine_code(df_lis_original["component_code"])
    ix_keep = engine_codes.notnull()
    lis_types_with_engine_code = df_lis_original.loc[ix_keep, "type_id"].unique()
    has_engine_code = np.isin(df_lis_matched["type_id"], lis_types_with_engine_code)
    lis_id_with_n_types = (
        df_lis_matched[has_engine_code]
        .groupby("type_id")
        .apply(lambda x: x["N-Type No."].unique())
    )
    percentage_matched = len(lis_id_with_n_types) / len(lis_types_with_engine_code) * 100
    logging.info(
        "For all LIS types that have an engine code, "
        f"{len(lis_id_with_n_types)}/{len(lis_types_with_engine_code)} "
        f"={percentage_matched}% get one or more N-types"
    )
    return percentage_matched
