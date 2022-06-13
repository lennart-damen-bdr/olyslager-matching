












# Critical cleaning
# - remove model info from the type column in LIS (already in the "model" column)
# -

# ----------------------- end of Thursday! ----------------------

# df_lis = remove_axel_config_from_type_lis(df_lis["type"])


# def remove_model_from_type_lis(df: pd.DataFrame) -> pd.DataFrame:
#     lower_type = df["type"].lower()
#     lower_model = df["model"].lower()
#     [t.replace(m, "") for t, m in zip(lower_type, lower_model)]


# Next, we will clean all strings


# str_cols = ["make", "model", "type", "category", "component_code"]
# for df in (df_tecdoc, df_lis):
#     df[str_cols] = df[str_cols].astype(str)
#     df[str_cols] = df[str_cols].apply(format_string_column)
#
#
#
# # For simplicity, we will drop all duplicates in LIS and TecDoc
# n_records = len(df_lis)
# df_lis = df_lis.drop_duplicates(subset=df_lis.columns[1:])
# n_records_dropped = n_records - len(df_lis)
# print(f"Number of duplicates dropped from LIS: {n_records_dropped} ({n_records_dropped/n_records*100}%)")
#
# n_records = len(df_tecdoc)
# df_tecdoc = df_tecdoc.drop_duplicates(subset=())
# n_records_dropped = n_records - len(df_tecdoc)
# print(f"Number of duplicates dropped from TecDoc: {n_records_dropped} ({n_records_dropped/n_records*100}%)")
#
# # Simplest idea: try to do exact matching
# matching_cols = ["model", "category", "model_year_start", "component_code"]    # "type", "make",
# df_tecdoc["in_tecdoc"] = True
# df_lis_matched = pd.merge(
#     left=df_lis,
#     right=df_tecdoc,
#     on=matching_cols,
#     how="left",
#     suffixes=("_lis", "_tecdoc")
# )
# print(f"# records in synthetic LIS before matching: {df_lis.shape[0]}")
# print(f"# records in synthetic LIS after matching: {df_lis_matched.shape[0]}")
# print(f"df_lis_matched['in_tecdoc'].sum(): {df_lis_matched['in_tecdoc'].sum()}")
#
# # print(f"# records in synthetic LIS with matched N-type: {}")
#
# # TODO compute this!
# lis_records_has_match = df_lis_matched.groupby(list(df_lis.columns))["in_tecdoc"]
# print(f"% records with at least one match: {df_lis_matched['in_tecdoc'].sum()/len(df_lis_matched)}")
#
#
# # Next, we will compute a number that indicates how much the model year overlaps
# # between LIS and TecDoc. If there is large overlap, we accept the match. If small overlap, we reject.
# # https://stackoverflow.com/questions/2953967/built-in-function-for-computing-overlap-in-python
# def get_percentage_interval_overlap(df: pd.DataFrame, start_col_1: str, start_col_2: str, stop_col_1: str, stop_col_2: str) -> pd.Series:
#     """Computes the percentage overlap between two intervals in a vectorized way
#
#     E.g. a = [10, 16]; b=[13, 20]. Then the overlapping part is [13, 16]. This has a length 3.
#     The length of the smallest interval is 6 (16-10). So the percentage overlap is 3/6 = 0.5 (50%)
#     """
#     abs_overlap = (df[[stop_col_1, stop_col_2]].min(axis=1) - df[[start_col_1, start_col_2]].max(axis=1)).clip(0, None)
#     smallest_interval_length = np.minimum(df[stop_col_1] - df[start_col_1], df[stop_col_2] - df[start_col_2])
#     return abs_overlap/smallest_interval_length


# TODO: for the POC, we drop all rows from LIS/TecDoc that do not have all the matching keys
# def keep_rows_all_keys(df: pd.DataFrame, name: str) -> pd.DataFrame:
#     df = df.copy(deep=True)
#     column_filled_percentage = df.notnull().mean(axis=0) * 100
#     print(f"Percentage of keys filled for {name}:\n{column_filled_percentage}")
#     all_keys_filled = df.notnull().all(axis=1)
#     filled_percentage = all_keys_filled.mean()
#     print(f"Percentage of rows with all keys filled {name}: {filled_percentage * 100}")
#     df = df.loc[all_keys_filled, :]
#     print(f"Dropped {(1 - filled_percentage) * 100} fraction of rows in {name} where at least one key was missing")
#     return df
#
#
# df_lis = keep_rows_all_keys(df_lis, "LIS")
# df_tecdoc = keep_rows_all_keys(df_tecdoc, "TecDoc")


# TODO: deal with axel configs that are not between brackets
# OLD
# def append_axel_config_lis(df: pd.DataFrame) -> tuple:
#     """Removes the axle configuration and appends it to the dataframe"""
#     df = df.copy(deep=True)
#     axels_between_brackets = (
#         df["type"]
#         .str.findall("\((.*?)\)")  # everything between brackets
#         .explode()  # if there are multiple () in one string, expand those into new elements
#         .dropna()
#         .replace("(", "")  # some axels configs look like 8x2(/4, we remove the (
#         .replace("-", "/")  # saw sometimes axel config = 8x4-4, replace the - by /
#         .str.findall("[0-9]x[0-9](?:/[0-9])?")  # find everything that looks like number x number (optional slash number)
#     )
#     ix_drop = axels_between_brackets.apply(lambda x: not x)
#     axels_between_brackets = axels_between_brackets.loc[~ix_drop]
#     axels_between_brackets = (  # some configs were specified as (4x4) (6x4), need to combine into [(4x4), (6x4)]
#         axels_between_brackets
#         .groupby(axels_between_brackets.index)
#         .sum()
#     )
#     axels_between_brackets.name = "axle_configuration"
#     assert not axels_between_brackets.index.duplicated().any()  # TODO: unit test
#     df = pd.concat([df, axels_between_brackets], axis=1)
#
#     return df