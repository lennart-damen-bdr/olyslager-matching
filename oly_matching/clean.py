import re
from typing import Union
import pandas as pd
from oly_matching import constants as c
from oly_matching import utils

ROMAN_NUMERALS = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}


def clean_whitespace(series: pd.Series) -> pd.Series:
    return (
        series
        .str.replace("\s+", " ")
        .str.lstrip()
        .str.rstrip()
    )


def clean_category_column_lis(series: pd.Series) -> pd.Series:
    return series.apply(clean_category_value_lis)


def clean_category_value_lis(x: str):
    for substring in ("Trucks and Buses (> 7.5t)", "Agricultural Equipment"):
        if substring in x:
            return substring
    return None


def clean_body_type_column_tecdoc(series: pd.Series) -> pd.Series:
    return series.replace(c.BODY_TYPE_CATEGORY_MAPPING)


def convert_time_cols_tecdoc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    for year_col in ("Model Year from", "Model Year to"):
        df[year_col] = df[year_col].dt.year
    return df


def format_string_column(series: pd.Series) -> pd.Series:
    series = series.copy(deep=True)
    series = series.str.lower()
    series = series.apply(remove_useless_characters)
    return series


def remove_useless_characters(x: str) -> str:
    """Removes all special characters, but keeps the ', ' (comma-space) intact"""
    words = [re.sub(r"[^a-zA-Z0-9]+", "", word) for word in x.split()]
    return " ".join(words)


def clean_make_column(make_series: pd.Series) -> pd.Series:
    """Removes everything between brackets, punctuation, and makes lowercase"""
    no_info_between_brackets = remove_substrings_with_accolades(make_series)
    clean_make_series = format_string_column(no_info_between_brackets)
    return clean_make_series


def remove_substrings_with_accolades(series: pd.Series) -> pd.Series:
    return series.str.replace("\((.*?)\)", "")


def remove_euro_code(series: pd.Series) -> pd.Series:
    clean_series = series.str.replace("\s[Ee]uro\s\d", "")
    clean_series = clean_whitespace(clean_series)
    return clean_series


def clean_model_column_lis(model_series: pd.Series) -> pd.Series:
    """Cleans the make column

    Assumes column has been converted to lower string already
    """
    clean_series = remove_euro_code(model_series)
    clean_series = remove_vehicle_type_lis(clean_series)
    clean_series = clean_whitespace(clean_series)
    return clean_series


def remove_vehicle_type_lis(model_series: pd.Series) -> pd.Series:
    clean_series = model_series.str.replace("|".join(c.VEHICLE_TYPES_LIS), "")
    clean_series = clean_whitespace(clean_series)
    return clean_series


def clean_model_column_tecdoc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    df["model"] = (
        df["model"]
        .str.replace("mp2\s\/\smp3", "")
        .str.replace("mp4\s\/\smp5", "ii")
    )
    for letter, number in ROMAN_NUMERALS.items():
        actros_letter = f"actros {letter} "
        actros_number = f"actros {number} "
        df["model"] = df["model"].str.replace(actros_number, actros_letter)
    df = utils.explode_column(df, col="model", delimiter="/")
    # df["model"] = remove_roman_numeral_from_end(df["model"])  # for MAN, careful to not mess up mercedes!
    df["model"] = clean_whitespace(df["model"])
    return df


def clean_type_column_lis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    df = get_type_without_model_column_lis(df)

    type_series = df["type"]
    type_series = remove_euro_code(type_series)
    type_series = remove_substrings_with_accolades(type_series)
    df["type"] = remove_axle_config_from_string(type_series)

    df["type"] = (
        df["type"]
        .str.replace("../", "")
        .apply(remove_useless_characters)
        .str.replace("\s+", "")
    )

    # df = explode_subtype_by_letter(df)
    return df


def clean_type_column_tecdoc(type_series: pd.Series) -> pd.Series:
    return (
        type_series
        .apply(remove_useless_characters)
        .str.replace("\s+", "")
    )


def remove_axle_config_from_string(series: pd.Series) -> pd.Series:
    return series.str.replace("|".join(c.UNIQUE_AXLE_CONFIGS), "")


def get_type_without_model_column_lis(df: pd.DataFrame) -> pd.Series:
    """Removes the 'model' from the 'type' column

    Both model and type column should be cleaned: lower string, removed axle config, no euro code
    """
    df = df.copy(deep=True)
    df["type"] = df.apply(
        lambda x: x["type"].replace(f"{x['model']} ", ""),
        axis=1
    )
    return df


def clean_engine_code_tecdoc(engine_series: pd.Series) -> pd.Series:
    engine_series = extract_mercedes_engine_code(engine_series)
    return engine_series


def clean_engine_code_lis(engine_series: pd.Series) -> pd.Series:
    engine_series = extract_mercedes_engine_code(engine_series)
    return engine_series


def extract_mercedes_engine_code(series: pd.Series) -> pd.Series:
    df_engine_codes = series.str.extract("([\d|x|X]{3}\.[\d|x|X]{3})")
    engine_series = df_engine_codes.iloc[:, 0].astype("string")
    return engine_series


def replace_none_like_string_with_none(series: pd.Series) -> pd.Series:
    return series.replace(to_replace=["nan", "None", "none"], value=None)


def explode_subtype_by_letter(df: pd.DataFrame) -> pd.Series:
    df["type"] = df["type"].str.replace("../", "")
    df["type"] = clean_whitespace(df["type"])
    # 3 or 4 digits, space, letters, optional slash letters repeated
    df["type_to_expand"] = df["type"].str.findall("\d{3,4}\s?\w+(?:/\w+)+")


def remove_roman_numeral_from_end(series: pd.Series) -> pd.Series:
    """See title. Only works for """
    roman_regex_group = "|".join(ROMAN_NUMERALS.keys())
    pattern = f"\s[{roman_regex_group}]+$"
    return series.str.replace(pattern, "")
