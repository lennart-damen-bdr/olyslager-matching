import pandas as pd

MERCEDES_MATCHING_COLS = ["make", "model", "type", "category", "component_code_clean"]


def match_mercedes(df_lis: pd.DataFrame, df_tecdoc: pd.DataFrame) -> pd.DataFrame:
    """Tries to match every record from lis against a record from tecdoc

    Assumes df_lis and df_tecdoc are already clean!
    """
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
            on=MERCEDES_MATCHING_COLS,
            suffixes=("_lis", "_tecdoc")
        )
        df_matched_list.append(df_lis_matched)

        df_lis_loop = df_lis_loop.drop(index=df_lis_i.index)
        df_lis_loop["component_code_clean"] = df_lis_loop["component_code_clean"].str[:-1]
        df_tecdoc["component_code_clean"] = df_tecdoc["component_code_clean"].str[:-1]
    df_lis_matched = pd.concat(df_matched_list)
    df_lis_matched = df_lis_matched.drop(columns=["component_code_clean"])
    return df_lis_matched
