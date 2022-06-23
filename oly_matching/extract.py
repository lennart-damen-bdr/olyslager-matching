from typing import Union
import logging
import pandas as pd
from oly_matching import constants as c


def append_axle_configs_lis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    n_records = len(df)
    logging.info(f"# records in LIS before appending axle config: {len(df)}")
    df["axle_configuration"] = df["type"].str.findall(c.AXLE_CONFIG_REGEX)
    df = df.explode(column="axle_configuration")
    df["axle_configuration_model_lis"] = df["model"].str.extract(c.AXLE_CONFIG_REGEX)
    logging.info(f"Added {len(df) - n_records} records, now LIS has {len(df)} records")
    return df


def extract_country_from_make_lis(make_series: pd.Series) -> pd.Series:
    """Returns if the make element contains a country from ALLOWED_COUNTRY_CODES

    To see how we came up with this list, run:
    >> between_brackets = make_series.str.findall("\((.*?)\)").explode()
    >> between_brackets.value_counts()
    You'll see the country codes there
    """
    return make_series.apply(lambda x: find_country(x))


def find_country(x: str) -> Union[str, None]:
    for country in c.ALLOWED_COUNTRY_CODES:
        if country in x:
            return country
    return None


def extract_euro_code(series: pd.Series) -> pd.Series:
    euro_series = series.str.findall(c.EURO_CODE_REGEX)
    is_null = euro_series.isnull()
    euro_series[is_null] = euro_series[is_null].apply(lambda x: [])
    euro_series = euro_series.apply(lambda x: None if not x else x[0])
    return euro_series


def extract_vehicle_type_lis(model_series: pd.Series) -> pd.Series:
    """Extracts the type of the vehicle (see constants VEHICLE_TYPES_LIS)

    For model column, assumes lowercase"""
    vehicle_type_list = []
    for vehicle_type in c.VEHICLE_TYPES_LIS:
        bool_series = model_series.str.contains(vehicle_type)
        string_series = bool_series.replace({True: vehicle_type, False: ""})
        vehicle_type_list.append(string_series)
    df_vehicle_types = pd.concat(vehicle_type_list, axis=1)
    vehicle_type_series = df_vehicle_types.apply(lambda x: ''.join(x), axis=1)
    return vehicle_type_series


def extract_and_append_relevant_data_lis(df: pd.DataFrame) -> pd.DataFrame:
    # Extract LIS information from columns that is needed for the merge, but don't modify the columns yet
    logging.info("Extracting and appending data to LIS...")
    df = df.copy(deep=True)
    df = append_axle_configs_lis(df)

    # Extract extra information from LIS, not necessarily needed for merge but nice to have
    for col in ("model", "component_code"):  # "type" for other brands than Mercedes
        df[f"euro_{col}_lis"] = extract_euro_code(df[col])
    for col in ("make", "category"):
        df[f"country_{col}_lis"] = extract_country_from_make_lis(df[col])
    df["vehicle_type_lis"] = extract_vehicle_type_lis(df["model"])
    logging.info("Extraction of LIS data completed successfully.")
    return df


def extract_mercedes_engine_code(series: pd.Series) -> pd.Series:
    df_engine_codes = series.str.extract("([\d|x|X]{3}\.[\d|x|X]{3})")
    engine_series = df_engine_codes.iloc[:, 0].astype("string")
    return engine_series


def extract_man_engine_code(series: pd.Series) -> pd.Series:
    df_engine_codes = series.str.extract("(d\s?\d{4}\s?[a-z]+\s?\d+)")
    engine_series = df_engine_codes.iloc[:, 0].astype("string")
    return engine_series


def get_type_format_tecdoc(df: pd.DataFrame) -> pd.Series:
    """Formats:
        1) the base type is stated once, the subtypes are repeated with comma's
            e.g. "28.280 fc, frc"
        2) types are split as a whole by comma's,
            e.g "19.293 fk,29.239 flk" or "24.350, 24.360"
    """
    is_multiple_types = df["type"].str.contains(",")
    split_type = df["type"].str.split(" ")
    first_words = split_type.apply(lambda x: x[0])
    other_words = split_type.apply(lambda x: " ".join(x[1:]))
    other_words_no_digits = ~other_words.str.contains("[0-9]+")
    df_words = pd.concat([df["type"], is_multiple_types, first_words, other_words, other_words_no_digits], axis=1)
    df_words.columns = ["type", "is_multiple_types", "first_word", "other_words", "other_words_no_digits"]

    format_series = pd.Series(index=df_words.index, name="tecdoc_format", dtype=int)
    format_series[~df_words["is_multiple_types"]] = 0
    format_series[
        df_words["is_multiple_types"]
        & df_words["other_words_no_digits"]
    ] = 1
    format_series[
        df_words["is_multiple_types"]
        & ~df_words["other_words_no_digits"]
    ] = 2
    return format_series
