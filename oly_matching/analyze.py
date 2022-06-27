import pandas as pd
from oly_matching import constants as c


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


def get_unique_property_per_id(df: pd.DataFrame, id_col: str, property_col: str) -> pd.Series:
    return df.groupby(id_col).apply(lambda x: x[property_col].unique()[0])


def get_performance_per_model(df_results: pd.DataFrame) -> pd.DataFrame:
    df = df_results.groupby(["make", "model"]).agg(
        {
            "type_id": "size",
            "has_engine_code": "sum",
            "has_at_least_one_match": ["sum", "mean"]
        }
    )
    df.columns = [
        "n_lis_ids", "n_lis_ids_with_engine_code", "n_lis_ids_with_one_or_more_n_types", "percentage_matched"
    ]
    df["percentage_matched"] = df["percentage_matched"] * 100
    df["percentage_matched_with_engine_code"] = df["n_lis_ids_with_one_or_more_n_types"] / df["n_lis_ids_with_engine_code"] * 100
    df["percentage_matched_with_engine_code"] = df["percentage_matched_with_engine_code"].fillna(0)
    df = df.round(2)
    df = df.sort_values(by="n_lis_ids", ascending=False)
    df = df.reset_index()
    df["n_lis_ids_with_one_or_more_n_types"].sum()/df["n_lis_ids_with_engine_code"].sum()
    return df


def get_links_and_original_data(df_matched: pd.DataFrame, df_lis_original: pd.DataFrame, df_tecdoc_original: pd.DataFrame) -> pd.DataFrame:
    type_id_n_type = (
        df_matched[["type_id", "N-Type No."]]
        .groupby(["type_id", "N-Type No."])
        .groups
        .keys()
    )
    df_links = pd.DataFrame(type_id_n_type, columns=["type_id", "N-Type No."])
    df_links = df_links[df_links["N-Type No."].notnull()]
    df_links["N-Type No."] = df_links["N-Type No."].astype(int)
    df_links = pd.merge(
        left=df_links,
        right=df_lis_original,
        on=["type_id"],
        how="inner"
    )
    df_links = pd.merge(
        left=df_links,
        right=df_tecdoc_original,
        on=["N-Type No."],
        how="left",
        suffixes=("_lis", "_tecdoc")
    )
    df_links = df_links[c.MATCHING_OUTPUT_COLUMNS]
    df_links = df_links.rename(columns={"axle_configuration": "axle_configuration_tecdoc"})
    return df_links
