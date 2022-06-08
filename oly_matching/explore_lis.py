import pandas as pd

df_lis = pd.read_excel("/Users/lennartdamen/Documents/code/olyslager/data/raw/lis.xlsx")
print(f"Lis: {df_lis.shape}")

# For POC, keep only the rows related to the engine
ix_keep = df_lis["component_group"] == "Engines"
df_lis = df_lis.loc[ix_keep, :]
print(f"Lis after dropping all rows that are not 'Engines': {df_lis.shape}")

# The type_id "almost" completely identifies a vehicle
value_count = df_lis.groupby('type_id').size().value_counts()
print(f"{value_count}")
# 1    16493
# 2       90
# 3        9
# 4        4
# 5        2
# value_count.iloc[0] / value_count.sum() > 99%, 16598 records

# I want to validate that the following columns correspond to a unique type_id
id_columns = [
    "make",
    "model",
    "type",
    # "type_year_start",
    # "type_year_end",
    "type_year_id",
    "component_code"  # code of the engine
]

# check how well these columns are filled: all, except engine 5% missing
filled_ratio = df_lis[id_columns].notnull().mean(axis=0)
print(filled_ratio)

unique_type_id_count = df_lis.groupby(id_columns).apply(lambda x: x["type_id"].nunique())
value_count = unique_type_id_count.value_counts()
# 1    14793
# 2      400
# 3       28
# 4       27
print(value_count)
print(value_count.iloc[0] / value_count.sum())  # > 99%, 16598 records
# That sounds good enough to me.
# For safety, we might want to check how a LIS type_id is generated EXACTLY but this works for now.
