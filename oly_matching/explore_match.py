import re
import pandas as pd
import numpy as np

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

VEHICLE_IDENTIFIER_COLUMNS_TECDOC = [
    "Manufacturer",
    "Model Series",
    "Type",
    "Body Type",
    "Model Year from",  # TODO: what does it mean if missing?
    "Model Year to",  # TODO: what does it mean if missing?
    "Engine Codes",
    "Tonnage",
    "Axle Configuration",
]

VEHICLE_IDENTIFIER_COLUMNS_LIS = [
    "make",
    "model",
    "type",
    "type_year_start",  # TODO: what does it mean if missing?
    "type_year_end",  # TODO: what does it mean if missing?
    "component_code"  # code of the engine
]


# Note: "type year" is not available in TecDoc, so we must make do with "model year"
MATCHING_COLUMN_MAPPING = {
    "Manufacturer": "make",
    "Model Series": "model",
    "Type": "type",  # granularity TecDoc < LIS
    "Body Type": "category",  # granularity TecDoc > LIS
    "Model Year from": "model_year_start",  # granularity TecDoc > granularity LIS (month vs year)
    "Model Year to": "model_year_end",  # granularity TecDoc > granularity LIS (month vs year)
    "Engine Codes": "component_code",
}

# For the moment, we only keep the columns we care about
df_lis = df_lis[MATCHING_COLUMN_MAPPING.values()]
df_tecdoc = df_tecdoc[MATCHING_COLUMN_MAPPING.keys()]

# Sync TecDoc and LIS time granularity
for year_col in ("Model Year from", "Model Year to"):
    df_tecdoc[year_col] = df_tecdoc[year_col].dt.year

# For the POC, we drop all rows from LIS/TecDoc that do not have all the matching keys
df_loop_dict = {"TecDoc": df_tecdoc, "LIS": df_lis}
for name, df in df_loop_dict.items():
    all_keys_filled = df.isnull().any(axis=1)
    filled_percentage = all_keys_filled.mean()
    print(f"Percentage of rows with all keys filled {name}: {filled_percentage * 100}")
    df = df.loc[all_keys_filled, :]
    print(f"Dropped {(1 - filled_percentage) * 100} fraction of rows in {name} where at least one key was missing")


# Next, we prepare the data from matching. We start with cleaning the "Body Type"/"category" pair
BODY_TYPE_CATEGORY_MAPPING = {
    'Platform/Chassis': "Trucks and Buses (> 7.5t)",
    'Truck Tractor': "Agricultural Equipment",
    'Dump Truck': "Trucks and Buses (> 7.5t)",
    'Bus': "Trucks and Buses (> 7.5t)",
    'Tractor': "Agricultural Equipment",
    'Municipal Vehicle': "Trucks and Buses (> 7.5t)",  # TODO
    'Concrete Mixer': "Agricultural Equipment",  # TODO
    'Bus Chassis': "Trucks and Buses (> 7.5t)",
    'Estate Van': "Trucks and Buses (> 7.5t)",
    'Cab with engine': "Trucks and Buses (> 7.5t)",  # TODO
}


def clean_category_column_lis(series: pd.Series) -> pd.Series:
    return series.apply(clean_category_value_lis)


def clean_category_value_lis(x: str):
    for substring in ("Trucks and Buses (> 7.5t)", "Agricultural Equipment"):
        if substring in x:
            return substring
    return None


def clean_body_type_column_tecdoc(series: pd.Series) -> pd.Series:
    return series.replace(BODY_TYPE_CATEGORY_MAPPING)


df_lis["category"] = clean_category_column_lis(df_lis["category"])
df_tecdoc["Body Type"] = clean_body_type_column_tecdoc(df_tecdoc["Body Type"])

# For simplicity, we will rename all tecdoc columns to correspond to LIS columns
df_tecdoc = df_tecdoc.rename(columns=MATCHING_COLUMN_MAPPING)


# Next, we will clean all strings
def format_string_column(series: pd.Series) -> pd.Series:
    series = series.copy(deep=True)
    series = series.str.lower()
    series = series.apply(remove_useless_characters)
    return series


def remove_useless_characters(x: str) -> str:
    """Removes all special characters, but keeps the ', ' (comma-space) intact"""
    words = [re.sub(r"[^a-zA-Z0-9]+", "", word) for word in x.split()]
    return " ".join(words)


str_cols = ["make", "model", "type", "category", "component_code"]
for df in (df_tecdoc, df_lis):
    df[str_cols] = df[str_cols].astype(str)
    df[str_cols] = df[str_cols].apply(format_string_column)


# Simplest idea: try to do exact matching
# TODO think about the direction of matching! left or right?
df_tecdoc["in_tecdoc"] = True
df_lis_matched = pd.merge(
    left=df_lis,
    right=df_tecdoc,
    on=["make", "model"],
    how="left"
)
print(f"# records before matching: {df_lis.shape[0]}")
print(f"# records after matching: {df_lis_matched.shape[0]}")

# TODO compute this!
lis_records_has_match = df_lis.groupby(VEHICLE_IDENTIFIER_COLUMNS_LIS)["in_tecdoc"]
print(f"% records with at least one match: {df_lis_matched['in_tecdoc'].sum()/len(df_lis_matched)}")


# Next, we will compute a number that indicates how much the model year overlaps
# between LIS and TecDoc. If there is large overlap, we accept the match. If small overlap, we reject.
# https://stackoverflow.com/questions/2953967/built-in-function-for-computing-overlap-in-python
def get_percentage_interval_overlap(df: pd.DataFrame, start_col_1: str, start_col_2: str, stop_col_1: str, stop_col_2: str) -> pd.Series:
    """Computes the percentage overlap between two intervals in a vectorized way

    E.g. a = [10, 16]; b=[13, 20]. Then the overlapping part is [13, 16]. This has a length 3.
    The length of the smallest interval is 6 (16-10). So the percentage overlap is 3/6 = 0.5 (50%)
    """
    abs_overlap = (df[[stop_col_1, stop_col_2]].min(axis=1) - df[[start_col_1, start_col_2]].max(axis=1)).clip(0, None)
    smallest_interval_length = np.minimum(df[stop_col_1] - df[start_col_1], df[stop_col_2] - df[start_col_2])
    return abs_overlap/smallest_interval_length
