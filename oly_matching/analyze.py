import pandas as pd


def get_lis_id_with_n_types(df_matched: pd.DataFrame) -> pd.DataFrame:
    df_matched = df_matched[df_matched["in_tecdoc"]]
    lis_id_with_n_types = (
        df_matched
        .groupby("type_id")
        .apply(lambda x: x["N-Type No."].unique())
    )
    return lis_id_with_n_types


def get_performance_per_model(df: pd.DataFrame) -> pd.DataFrame:
    performance_per_model = df.groupby("model")["is_matched"].mean().round(2) * 100
    matched_per_model = df.groupby("model")["is_matched"].sum()
    types_per_model = df.grupby("model").size()
    types_per_model.name = "count unique ids"
    performance_per_model.name = "% ids matched"
    matched_per_model.name = "# ids matched"
    df_performance = pd.concat([matched_per_model, performance_per_model, types_per_model], axis=1)
    df_performance = df_performance.sort_values(by="count unique ids", ascending=False)
    return df_performance
