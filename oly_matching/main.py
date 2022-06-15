import numpy as np
import pandas as pd

from oly_matching import constants as c
from oly_matching import clean, extract, utils

# TODO: ignoring country codes for matching for now! Check if okay

df_tecdoc = pd.read_excel(
    io="/Users/lennartdamen/Documents/code/olyslager/data/raw/tecdoc.xlsx",
    parse_dates=[7, 8]
)
df_lis = pd.read_excel("/Users/lennartdamen/Documents/code/olyslager/data/raw/lis.xlsx")


print(f"Tecdoc: {df_tecdoc.shape}")
print(f"Lis: {df_lis.shape}")

# For POC, keep only the rows related to the engine
ix_keep = df_lis["component_group"] == "Engines"
df_lis = df_lis.loc[ix_keep, :]
print(f"Lis after dropping all rows that are not 'Engines': {df_lis.shape}")

# For the moment, we only keep the columns we care about
lis_cols = [x for x in c.MATCHING_COLUMN_MAPPING.values() if x != "axle_configuration"]
lis_cols += ["type_id"]
df_lis = df_lis[lis_cols]

tecdoc_cols = list(c.MATCHING_COLUMN_MAPPING.keys())
tecdoc_cols += ["N-Type No."]
df_tecdoc = df_tecdoc[tecdoc_cols]

df_tecdoc = clean.convert_time_cols_tecdoc(df=df_tecdoc)

# For simplicity, we will rename all tecdoc columns to correspond to LIS columns
df_tecdoc = df_tecdoc.rename(columns=c.MATCHING_COLUMN_MAPPING)

# For inspection, we sort the data
# df_lis = df_lis.sort_values(by=list(df_lis.columns))
# df_tecdoc = df_tecdoc.sort_values(by=list(df_tecdoc.columns))

# For further cleaning, we focus on the largest brands (=make) in LIS
n_records_per_brand = df_lis["make"].value_counts(ascending=False)
print(f"The ten biggest brands in LIS are:\n{n_records_per_brand.iloc[:10]}")
print("We will take extra care trying to get the formatting between LIS and TecDoc right for those brands")

# Take one of the largest brands. Done: "mercedes -> 15%
# ix_keep = df_tecdoc["make"] == "MAN"
ix_keep = df_lis["make"].str.lower().str.contains("mercedes")
df_lis = df_lis.loc[ix_keep, :]

ix_keep = df_tecdoc["make"].str.lower().str.contains("mercedes")
df_tecdoc = df_tecdoc.loc[ix_keep, :]

# Save the original data to compare matches later
df_lis_original = df_lis.copy(deep=True)
df_tecdoc_original = df_tecdoc.copy(deep=True)

# Extract LIS information from columns that is needed for the merge, but don't modify the columns yet
df_lis = extract.append_axle_configs_lis(df_lis)

# Extract extra information from LIS, not necessarily needed for merge but nice to have
for col in ("model", "component_code"):  # "type" for other brands than Mercedes
    df_lis[f"euro_{col}_lis"] = extract.extract_euro_code(df_lis[col])
df_lis["country_lis"] = extract.extract_country_from_make_lis(df_lis["make"])
df_lis["vehicly_type_lis"] = extract.extract_vehicle_type_lis(df_lis["model"])


# For simple cleaning we use hardcoding
df_lis["category"] = clean.clean_category_column_lis(df_lis["category"])
df_tecdoc["category"] = clean.clean_body_type_column_tecdoc(df_tecdoc["category"])

# Clean the columns from LIS and TecDoc so that they have the same format
df_lis[c.STR_COLS] = (
    df_lis[c.STR_COLS]
    .astype("string")
    .apply(lambda x: x.str.lower())
)
df_tecdoc[c.STR_COLS] = (
    df_tecdoc[c.STR_COLS]
    .astype("string")
    .apply(lambda x: x.str.lower())
)
for col in c.STR_COLS:
    df_lis[col] = clean.clean_whitespace(df_lis[col])
    df_tecdoc[col] = clean.clean_whitespace(df_tecdoc[col])

for col in ("type", "component_code"):
    df_lis = utils.explode_column(df_lis, col)
    df_tecdoc = utils.explode_column(df_tecdoc, col)

df_lis["make"] = clean.clean_make_column(df_lis["make"])
df_tecdoc["make"] = clean.clean_make_column(df_tecdoc["make"])

df_lis["model"] = clean.clean_model_column_lis(df_lis["model"])
df_tecdoc = clean.clean_model_column_tecdoc(df_tecdoc)

# TODO: expand the subtypes separated by XXXX letters/letters, or just letters/letters
df_lis = clean.clean_type_column_lis(df_lis)
df_tecdoc["type"] = clean.clean_type_column_tecdoc(df_tecdoc["type"])

df_tecdoc["component_code"] = clean.clean_engine_code_tecdoc(df_tecdoc["component_code"])
df_lis["component_code"] = clean.clean_engine_code_lis(df_lis["component_code"])

# Matching
# If the type is missing, we remove the row
REQUIRED_COLS = ["make", "model", "type", "component_code"]

ix_keep = df_tecdoc[REQUIRED_COLS].notnull().all(axis=1)
df_tecdoc = df_tecdoc[ix_keep]
df_tecdoc["in_tecdoc"] = True

ix_keep = df_lis[REQUIRED_COLS].notnull().all(axis=1)
df_lis = df_lis[ix_keep]

MATCHING_COLS = ["make", "model", "type", "category", "component_code_clean"]

df_lis_loop = df_lis.copy(deep=True)
df_lis_loop = df_lis_loop.reset_index(drop=True)
df_tecdoc = df_tecdoc.reset_index(drop=True)
# Previously: just match. But for mercedes need to deal with wildcards!
df_lis_loop["component_code_clean"] = df_lis_loop["component_code"].copy(deep=True)
df_tecdoc["component_code_clean"] = df_tecdoc["component_code"].copy(deep=True)

# Handling wildcards for Mercedes in LIS. Assumes TecDoc does NOT have any wildcards
df_matched_list = []
while df_lis_loop.shape[0] != 0:
    row_ends_with_wildcard = df_lis_loop["component_code_clean"].str[-1] == "x"
    df_lis_i = df_lis_loop[~row_ends_with_wildcard]

    df_lis_matched = pd.merge(
        left=df_lis_i,
        right=df_tecdoc,
        how="left",
        on=MATCHING_COLS,
        suffixes=("_lis", "_tecdoc")
    )
    df_matched_list.append(df_lis_matched)

    df_lis_loop = df_lis_loop.drop(index=df_lis_i.index)
    df_lis_loop["component_code_clean"] = df_lis_loop["component_code_clean"].str[:-1]
    df_tecdoc["component_code_clean"] = df_tecdoc["component_code_clean"].str[:-1]

df_lis_matched = pd.concat(df_matched_list)
df_lis_matched["in_tecdoc"] = df_lis_matched["in_tecdoc"].replace(to_replace=[None], value=False)

for col in ("model_year_start", ):  # , "model_year_end"
    diff_in_years = df_lis_matched[f"{col}_lis"] - df_lis_matched[f"{col}_tecdoc"]
    ix_keep = (diff_in_years.abs() <= 5) | (diff_in_years.isnull())
    print(f"Dropping {len(df_lis_matched) - ix_keep.sum()} rows because model years to far apart")
    df_lis_matched = df_lis_matched[ix_keep]

ix_keep = (
    df_lis_matched["axle_configuration_lis"].isnull()
    | (df_lis_matched["axle_configuration_lis"] == df_lis_matched["axle_configuration_tecdoc"])
)
print(f"Dropping {ix_keep.sum()}/{df_lis_matched.shape[0]} records because axle config not matching")
df_lis_matched = df_lis_matched[ix_keep]

df_matched = df_lis_matched[df_lis_matched["in_tecdoc"]]
lis_id_with_n_types = df_matched.groupby("type_id").apply(lambda x: x["N-Type No."].unique())
unique_lis_types = df_lis_original["type_id"].unique()

print(f"Perentage matched = {len(lis_id_with_n_types)}/{len(unique_lis_types)} = {len(lis_id_with_n_types)/len(unique_lis_types)*100}%")

# Analyze not matched LIS ID's
unmatched_lis_ids = [x for x in unique_lis_types if x not in lis_id_with_n_types.index]
lis_record_is_not_matched = np.isin(df_lis_original["type_id"], unmatched_lis_ids)
df_lis_original["is_matched"] = ~lis_record_is_not_matched

performance_per_model = df_lis_original.groupby("model")["is_matched"].mean().round(2)
types_per_model = df_lis_original.groupby("model").size()
# performance_per_model = df_lis_original.groupby("model")["is_matched"].mean().round(2)
# types_per_model = df_lis_original.groupby("model").size()
types_per_model.name = "count unique ids"
performance_per_model.name = "% ids matched"
df_performance = pd.concat([performance_per_model, types_per_model], axis=1)
df_performance = df_performance.sort_values(by="count unique ids", ascending=False)
df_performance.to_excel("/Users/lennartdamen/Documents/code/olyslager/data/raw/mercedes_matching_performance_15_06_2022.xlsx")

# lis_record_is_not_matched = np.isin(df_lis["type_id"], unmatched_lis_ids)
# df_lis["is_matched"] = ~lis_record_is_not_matched
#
# ix_keep = (
#     (df_lis["model"] == "atego")
#     & (df_lis["type"] == "1018ko")
#     & (df_lis["category"] == "trucks and buses (> 7.5t)")
# )
# df_lis_i = df_lis[ix_keep].sort_values(by=["model", "type"])
#
# ix_keep = (
#     (df_tecdoc["model"] == "atego")
#     & (df_tecdoc["type"] == "1018ko")
#     & (df_tecdoc["category"] == "trucks and buses (> 7.5t)")
# )
# df_tecdoc_i = df_tecdoc[ix_keep].sort_values(by=["model", "type"])
#
# ix_keep = df_tecdoc_original["model"] == "ACTROS"
# actros_count_tecdoc = df_tecdoc_original.loc[ix_keep, "component_code"].value_counts()
#
# ix_keep = df_lis_original["model"] == "Actros"
# actros_count_lis = df_lis_original.loc[ix_keep, "component_code"].value_counts()

# Mercedes examples:
# Example 1 (14 June): model_year too strict
# example_id = unmatched_lis_ids[100]
# ix_keep = df_lis_original["type_id"] == example_id
# df_lis_example = df_lis_original[ix_keep]
#
# ix_keep = (
#     df_tecdoc_original["model"].str.lower().str.contains("sk")
#     & (df_tecdoc_original["type"].str.contains("2638"))
#     & df_tecdoc_original["component_code"].str.lower().str.contains("402")
#     & (df_tecdoc_original["axle_configuration"] == "6x4")
# ).fillna(False)
# df_tecdoc_example = df_tecdoc_original[ix_keep].drop_duplicates()
#
# # Example 2 (14 June): no matching engine code
# example_id = unmatched_lis_ids[512]
# ix_keep = df_lis_original["type_id"] == example_id
# df_lis_example = df_lis_original[ix_keep]
#
# ix_keep = (
#     df_tecdoc_original["model"].str.contains("lk")
#     & (df_tecdoc_original["type"] == "917")
#     # & df_tecdoc["component_code"].str.contains("om366")
# )
# df_tecdoc_example = df_tecdoc_original[ix_keep].drop_duplicates()
#
# # Example 3 (14 June): goes wrong because of k/s (converted to ks)
# example_id = unmatched_lis_ids[200]
# ix_keep = df_lis_original["type_id"] == example_id
# df_lis_example = df_lis_original[ix_keep]
#
# ix_keep = (
#     df_tecdoc_original["model"].str.contains("actros")
#     & df_tecdoc_original["type"].str.contains("3332")
#     # & (df_tecdoc["axle_configuration"] == "6x4")
#     # & df_tecdoc["component_code"].str.contains("om366")
# )
# df_tecdoc_example = df_tecdoc_original[ix_keep].drop_duplicates()

# Mercedes-Benz
# - LIS
# --- make = Mercedes-Benz (COUNTRY)
# --- the country code is in capital between brackets
# --- model can contain 'Euro x' code, e.g. Atego Euro 5 (looks like always formatted with space)
# --- model can contain something like Construction/Chassis/tractor, like Actros II tractor Euro 6
# --- model is sometimes repeated in the type, but also often not (50-50?)
# --- type can contains L/LL/LS/K or jus LS
# --- type can contain the axle config, usually between brackets or sometimes separated by space
# --- type can also contain other info between brackets, such as (chassis), (tractor)
# --- component_code is formatted mostly like OMxxxLA, somtimes follow by a generation in Roman (IV)
# --- the component_code ALSO often contains Euro x after OMxxxLA.
#     Sometimes Euro x is in type, sometimes in component, sometimes both

# TecDoc
# --- make = MERCEDES-BENZ
# --- model = capitals, sometimes seperated by slash or space-slash-space
#             example: T2/L or ACTROS MP2 / MP3.
# --- model sometimes has an O NUMBER between brackets, like CONECTO () 345)
# --- In the vast majority, the model is NOT repeated in the type.
#     Ocassionally it IS repeated, like INTEGRO (0 550) - Integro
# --- component_code is formatted OM xxx.xxx in all cases I could see
# --- component_code my have info between brackets, like OM xxx.xxx (xx.xx-xx.xx)

# Plan
# --- only add new columns followed by suffix "_merge"
# --- extract and remove (COUNTRY) from LIS
# --- extract and remove Euro x from model and component_code from LIS
# --- extract and remove Construction/Chassis/tractor from model LIS
# --- remove model from the type column from LIS
# --- expand the slashes in the L/LL/LS/K (Tecdoc has xxxx AK or xxxxx S)
# --- for both, add a component_code column that looks like OMxxx (forgetting LA and more specific engine codes)

# MAN
# LIS
# - make can contain (BRA), but other than that fine
# - model can contain Euro code
# - type contains the model
# - type: after the model, there's digit(s).digits space LETTER(optional /LETTERS/...)
# - type can contain Euro code
# - type can contain SCR/EGR/...? /EEV?
# - type can contain the axle config (most records this is true)
# - type can be split by comma, e.g. TGX 26.420, 26,480, 26.500 (6x4 BB) Euro 6 --> what is BB?
# - type can be split by comma, e.g. TGS 35.430, 35.470, 35.510 BL,BB (8x4) (LK,TM) Euro 6d --> how to split this?
# - component_code almost always split by comma
# - component code can contain Euro code
# - component code can have different formats, e.g. 224 (D0826 LFL03 Euro 2), D 0826 LF 08, 313 (MAN D2866 LF26/EDC/Euro3)

# TecDoc
# - model TG(letter) I/II,
# - component code looks like D 4-digits LETTER/DIGIT-code
# - component code can be separated by comma
