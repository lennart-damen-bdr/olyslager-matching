import pandas as pd

df_tecdoc = pd.read_excel("/Users/lennartdamen/Documents/code/olyslager/data/raw/tecdoc.xlsx")
for date_col in ("Model Year from", "Model Year to"):
    df_tecdoc[date_col] = pd.to_datetime(df_tecdoc[date_col])
df_tecdoc["Year ID"] = df_tecdoc["Model Year from"].astype(str) + "_" + df_tecdoc["Model Year from"].astype(str)

# Identify the columns that determine a row completely
tecdoc_id_columns = [
    "Manufacturer",
    "Model Series",
    "Type",
    "Body Type",
    "Year ID",
    "Engine Codes",
    "Tonnage",
    "Axle Configuration",
]


def compute_n_type_count_per_group(df: pd.DataFrame, id_columns: list) -> pd.Series:
    df = df.copy(deep=True)
    df[id_columns] = df[id_columns].astype(str)
    df_count = df.groupby(id_columns).size()
    df_count.name = "count"
    df_count = df_count.reset_index()
    return df_count

df_count_per_group = compute_n_type_count_per_group(
    df=df_tecdoc, id_columns=tecdoc_id_columns
)
count_distribution = df_count_per_group["count"].value_counts()
print(count_distribution)
# Gives a count of
# 1    27805
# 2      103
# 3        9
# 5        3
# 4        1


# Hypothesis: duplicates are due to missing key
df_strange_records = df_count_per_group.loc[df_count_per_group["count"] > 1, :]

# Note: the Type sometimes has comma's in the name for strange records. Might need to explode those comma's
# Note: Lot of duplicates with missing Engine Code

# Checking what happens if we drop the records with missing engine codes
ix_keep = df_tecdoc["Engine Codes"].notnull()
df_filtered = df_tecdoc.loc[ix_keep, :]
df_filtered_count_per_group = compute_n_type_count_per_group(df=df_filtered, id_columns=tecdoc_id_columns)
print(df_filtered_count_per_group["count"].value_counts())
# Gives count of
# 1    26284
# 2       64
# 3        8
# 5        3
# For me, that's acceptable. We can dig deeper, but for now we stop looking further.

# What if we drop the Engine Codes?
id_cols_no_engine = [x for x in tecdoc_id_columns if x != "Engine Codes"]
df_count_no_engine = compute_n_type_count_per_group(df=df_tecdoc, id_columns=id_cols_no_engine)
value_count = df_count_no_engine["count"].value_counts()
print(value_count)
# Then this count
# 1    24853
# 2      996
# 3      181
# 4       65
# 5       46
# 6       15
# 7        7
# 8        5
# value_count.iloc[0] / value_count.sum() =~ 95%

# What if we only use columns that we directly have available in LIS?
minimal_id_cols = [
    "Manufacturer",
    "Model Series",
    "Type",
    "Body Type",
    "Year ID",
    "Engine Codes"
]
df_count_no_engine = compute_n_type_count_per_group(df=df_tecdoc, id_columns=minimal_id_cols)
value_count = df_count_no_engine["count"].value_counts()
print(value_count)
# Then this count
# 1     17676
# 2      2419
# 3       533
# 4       222
# 5       106
# ...     ...
# value_count.iloc[0] / value_count.sum() =~ 83%
# which means that if a client asks for a report, in a bit more than 30% of the cases
# he will have to choose from more vehicles than necessary ASSUMING OUR MATCHING IS PERFECT

# Check if columns that represent an ID are really an ID
all(df_tecdoc["Type No."].value_counts() == 1)
all(df_tecdoc["N-Type No."].value_counts() == 1)

id_pairs = (
    ("Engine Type", "Engine Type ID"),
    ("Axle Configuration", "Axle Configuration ID"),
    ("Body Type", "Body Type ID"),
)

for col_1, col_2 in id_pairs:
    df_unique_pairs = df_tecdoc[[col_1, col_2]].drop_duplicates()
    assert all(df_unique_pairs.groupby(col_1).count() == 1)
    assert all(df_unique_pairs.groupby(col_2).count() == 1)


# --- Mess below, warning. Results of exploring which columns work
# Still not unique, see N types [36906, 36895, 36874, 36867, 36860, 36905, 36894, 36873, 36866, 36859]
# At first sight looks like kW is the differentiator, but still not true:
# strange_n_types = [36906, 36895, 36874, 36867, 36860, 36905, 36894, 36873, 36866, 36859]
# ix = df_tecdoc["N-Type No."].apply(lambda x: x in strange_n_types)
# ix = ix & (df_tecdoc["kW from"] == 183)
# df_strange = df_tecdoc.loc[ix, :]

# tecdoc_id_columns = [
#     "Manufacturer",
#     "Model Series",
#     "Type",
#     "Engine Codes",
#     "Tonnage",
#     "Axle Configuration",
#     "Year ID",
# ]

# Hypothesis: all duplicates are caused by wrong entries: looks like Year from == Year to everywhere
# Hypothesis wrong: see N-Type 12720, 12721: The Body Type differs!


# Not tecdoc_id_columns = ["Manufacturer", "Model Series", "Type"], see example below
# ix = (
#     (df_tecdoc["Manufacturer"].astype(str) == "ALEXANDER DENNIS")
#     & (df_tecdoc["Model Series"].astype(str) == "ENVIRO200")
#     & (df_tecdoc["Type"].astype(str) == "200")
# )
# Adding the Engine Code is still not enough (see Engine Code ISBe6-250, N-Type No. 47531 and 57530)
# Adding year from and to still not (same example)
# Only thing that differs is the tonnage!

# Not tecdoc_id_columns = ["Manufacturer", "Model Series", "Type", "Engine Codes]
# ix = (
#     (df_tecdoc["Manufacturer"].astype(str) == "DENNIS")
#     & (df_tecdoc["Model Series"].astype(str) == "ELITE 2")
#     & (df_tecdoc["Type"].astype(str) == "290")
#     & (df_tecdoc["Engine Codes"].astype(str) == "D7E290")
# )

# For this example, it seems like we need to add Tonnage AND Axle Configuration
# See N-type no. 20713 and 9345 (the tonnage is the same, but only the axle is different)

# Also not tecdoc_id_columns = ["Manufacturer", "Model Series", "Type", "Engine Codes", "Tonnage", "Axle Configuration"]
# ix = (
#     (df_tecdoc["Manufacturer"].astype(str) == "ALEXANDER DENNIS")
#     & (df_tecdoc["Model Series"].astype(str) == "ENVIRO400")
#     & (df_tecdoc["Type"].astype(str) == "400")
#     & (df_tecdoc["Engine Codes"].astype(str) == "ISBe6-250")
#     & (df_tecdoc["Tonnage"].astype(str) == "18.0")
# )
# Need to add model year

# Also not
# tecdoc_id_columns = [
#     "Manufacturer",
#     "Model Series",
#     "Type",
#     "Engine Codes",
#     "Tonnage",
#     "Axle Configuration",
#     "Model Year from",
#     "Model Year to"
# ]
# ix = (
#     (df_tecdoc["Manufacturer"].astype(str) == "VOLVO")
#     & (df_tecdoc["Model Series"].astype(str) == "FH16")
#     & (df_tecdoc["Type"].astype(str) == "FH 16/700")
#     & (df_tecdoc["Engine Codes"].astype(str) == "D16G700")
#     & (df_tecdoc["Tonnage"].astype(str) == "34.0")
# )
