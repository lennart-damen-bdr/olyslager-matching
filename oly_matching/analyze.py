import pandas as pd


def get_lis_id_with_n_types(df_matched: pd.DataFrame) -> pd.DataFrame:
    df_matched = df_matched[df_matched["in_tecdoc"]]
    lis_id_with_n_types = (
        df_matched
        .groupby("type_id")
        .apply(lambda x: x["N-Type No."].unique())
    )
    return lis_id_with_n_types


def get_lis_id_has_engine_code(df: pd.DataFrame, id_col: str, engine_col: str = "component_code") -> pd.Series:
    has_at_least_one_engine_code = df.groupby(id_col).apply(lambda x: x[engine_col].notnull().any())
    has_at_least_one_engine_code.name = "has_engine_code"
    return has_at_least_one_engine_code
