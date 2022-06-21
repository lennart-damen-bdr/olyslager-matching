import re
import logging
import pandas as pd
from oly_matching import constants as c
from oly_matching import utils

ROMAN_NUMERALS = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}


def keep_engine_records_lis(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Dropping all LIS records that are not related to the engine...")
    df = df.copy(deep=True)
    ix_keep = df["component_group"] == "Engines"
    logging.info(f"Lis after dropping {len(df) - ix_keep.sum()} rows that are not 'Engines': {df.shape}")
    df = df.loc[ix_keep, :]
    return df


# TODO: change this function according to which records you want to match
#  currently, we only keep records for mercedes-benz
def filter_records(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    # ix_keep = df["make"].str.lower().str.contains("mercedes")
    ix_keep = df["make"] == "MAN"
    df = df.loc[ix_keep, :]
    return df


def clean_whitespace(series: pd.Series) -> pd.Series:
    return (
        series
        .str.replace("\s+", " ", regex=True)
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


def clean_category_column_tecdoc(series: pd.Series) -> pd.Series:
    return series.replace(c.CATEGORY_MAPPING)


def convert_time_cols_tecdoc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    for year_col in ("Model Year from", "Model Year to"):
        df[year_col] = df[year_col].dt.year
    return df


def format_string_column(series: pd.Series) -> pd.Series:
    series = series.copy(deep=True)
    series = series.str.lower()
    series = series.apply(remove_special_characters)
    return series


def remove_special_characters(x: str) -> str:
    """Removes all special characters, but keeps the ', ' (comma-space) intact"""
    words = [re.sub(r"[^a-zA-Z0-9]+", "", word) for word in x.split()]
    return " ".join(words)


def clean_make_column(make_series: pd.Series) -> pd.Series:
    """Removes everything between brackets, punctuation, and makes lowercase"""
    no_info_between_brackets = remove_substrings_with_accolades(make_series)
    clean_make_series = format_string_column(no_info_between_brackets)
    return clean_make_series


def remove_substrings_with_accolades(series: pd.Series) -> pd.Series:
    return series.str.replace("\((.*?)\)", "", regex=True)


def remove_euro_code(series: pd.Series) -> pd.Series:
    clean_series = series.str.replace("\s[Ee]uro\s\d", "", regex=True)
    clean_series = clean_whitespace(clean_series)
    return clean_series


def clean_model_column_lis(model_series: pd.Series) -> pd.Series:
    """Cleans the make column

    Assumes column has been converted to lower string already
    """
    clean_series = remove_euro_code(model_series)
    clean_series = remove_vehicle_type_lis(clean_series)
    clean_series = clean_whitespace(clean_series)
    clean_series = clean_series.replace("tgl/4", "tgl")
    return clean_series


def remove_vehicle_type_lis(model_series: pd.Series) -> pd.Series:
    clean_series = model_series.str.replace("|".join(c.VEHICLE_TYPES_LIS), "", regex=True)
    clean_series = clean_whitespace(clean_series)
    return clean_series


def clean_model_column_tecdoc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    df["model"] = (
        df["model"]
        .str.replace("mp2\s\/\smp3", "", regex=True)
        .str.replace("mp4\s\/\smp5", "ii", regex=True)
    )
    for letter, number in ROMAN_NUMERALS.items():
        actros_letter = f"actros {letter} "
        actros_number = f"actros {number} "
        df["model"] = df["model"].str.replace(actros_number, actros_letter, regex=True)
    df = utils.explode_column(df, col="model", delimiter="/")  # for mercedes, possibly for other makes
    df = _clean_model_column_tecdoc_man(df)
    df["model"] = clean_whitespace(df["model"])
    return df


def _clean_model_column_tecdoc_man(df: pd.DataFrame) -> pd.DataFrame:
    is_man_record = df["make"] == "man"
    if is_man_record.sum() > 0:
        df_man = df[is_man_record]
        df_rest = df[~is_man_record]
        df_man["model"] = remove_roman_numeral_from_end(df["model"])
        is_m2000_row = df_man["model"].str.startswith("m 2000")
        df_man.loc[is_m2000_row, "model"] = "m2000"
        df = pd.concat([df_rest, df_man])
    return df


def clean_type_column_lis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    df = get_type_without_model_column_lis(df)

    type_series = df["type"]
    type_series = remove_euro_code(type_series)
    type_series = remove_substrings_with_accolades(type_series)
    type_series = remove_axle_config_from_string(type_series)
    type_series = clean_whitespace(type_series)
    df["type"] = type_series.str.replace("\.\./", "", regex=True)
    df = expand_type_column(df)

    df["type"] = (
        df["type"]
        .apply(remove_special_characters)
        .str.replace("\s+", "", regex=True)
    )
    return df


def expand_type_column(df: pd.DataFrame) -> pd.DataFrame:
    """Actros is split by slash, arocs by comma. Treat carefully!

    Split by /: atego, actros (optional space), axor,
    Split by ,: actros ii, arocs, and antos (xxxx, xxxx, xxxx LS)
    """
    df = df.copy()

    # Deal with comma separated types
    is_comma_separated = (
        (df["type"].str.match("^\d+,\s"))
        # & (np.isin(df_rest["model"], ["actros ii", "arocs", "antos"]))  # TODO: improves mercedes but kills general
    )
    df_comma = df[is_comma_separated]
    df_comma = expand_comma_separated_types(df_comma)

    # Deal with slash separated types
    df_rest = df[~is_comma_separated]
    is_slash_separated = (
        (df_rest["type"].str.contains("\w+\s?/"))
        # & (np.isin(df_rest["model"], ["atego", "actros", "axor"]))  # TODO: improves mercedes but kills general
    )
    df_slash = df_rest[is_slash_separated].copy(True)
    df_slash = expand_slash_separated_types(df_slash)

    # Merge results
    df_rest = df_rest[~is_slash_separated]
    df_clean = pd.concat([df_rest, df_comma, df_slash], axis=0)
    df_clean = df_clean.loc[:, df.columns]
    return df_clean


def expand_slash_separated_types(df: pd.DataFrame) -> pd.DataFrame:
    split_type = df["type"].str.split("\s+").copy(True)
    df["base_type"] = split_type.apply(lambda x: x[0])
    df["subtypes"] = (
        split_type
        .apply(lambda x: x[1])
        .str.split("\s?/\s?")
    )
    df = df.explode(column="subtypes")
    df["type"] = df["base_type"] + " " + df["subtypes"]
    return df


def expand_comma_separated_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    df["base_types"] = (
        df["type"].copy(deep=True)
        .str.findall("^\d{4}(?:,\s\d{4})+")
        .apply(lambda x: x[0] if x else "")
        .str.split(", ")
    )
    df["stripped_type"] = (
        df["type"].copy(deep=True)
        .str.replace("^\d{4}(?:,\s\d{4})+\s", "", regex=True)
    )
    df["sub_type"] = (
        df["stripped_type"]
        .copy(deep=True)
        .str.split(" ")
        .apply(lambda x: x[0])
        .str.extract("^(\w+)")
        .fillna("")
    )
    df = df.explode(column="base_types")
    df["type"] = df["base_types"] + " " + df["sub_type"]
    return df


def clean_type_column_tecdoc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    # TODO: how to deal with MAN
    is_man_record = df["make"] == "man"
    df_man = df[is_man_record]

    # split_type = df_man["type"].str.split(" ").copy(deep=True)
    # first_type_element = split_type.apply(lambda x: x[0])
    # has_base_with_subtype_format = (
    #     first_type_element.str.contains("^\d+")
    #     & first_type_element.str.contains("\.")
    # )
    # df_man_format = df_man[has_base_with_subtype_format]
    # df_man_format["base_type"] = (
    #     first_type_element[has_base_with_subtype_format]
    #     .str.replace(",", "")
    # )
    # df_man_rest = df_man[~has_base_with_subtype_format]

    df = utils.explode_column(df, "type")  # used for mercedes
    df["type"] = (
        df["type"]
        .apply(remove_special_characters)
        .str.replace("\s+", "", regex=True)
    )
    return df


def remove_axle_config_from_string(series: pd.Series) -> pd.Series:
    return series.str.replace("|".join(c.UNIQUE_AXLE_CONFIGS), "", regex=True)


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


def clean_engine_code(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(deep=True)
    df = utils.explode_column(df, "component_code")

    is_mercedes_record = df["make"] == "mercedes"
    df_mercedes = df[is_mercedes_record]
    df_mercedes["component_code"] = extract_mercedes_engine_code(df_mercedes["component_code"])

    # TODO: deal with component codes separated by / for MAN
    df_rest = df[~is_mercedes_record]
    is_man_record = df_rest["make"] == "man"
    df_man = df_rest[is_man_record]
    df_rest = df_rest[~is_man_record]
    df_man["component_code"] = df_man["component_code"].str.extract("(d\s?\d{4}\s?[a-z]+\s?\d+)")

    df = pd.concat([df_mercedes, df_man, df_rest], axis=0)
    df["component_code"] = df["component_code"].str.replace(" ", "")

    return df


def extract_mercedes_engine_code(series: pd.Series) -> pd.Series:
    df_engine_codes = series.str.extract("([\d|x|X]{3}\.[\d|x|X]{3})")
    engine_series = df_engine_codes.iloc[:, 0].astype("string")
    return engine_series


def replace_none_like_string_with_none(series: pd.Series) -> pd.Series:
    return series.replace(to_replace=["nan", "None", "none"], value=None)


def remove_roman_numeral_from_end(series: pd.Series) -> pd.Series:
    """See title. Only works for """
    roman_regex_group = "|".join(ROMAN_NUMERALS.keys())
    pattern = f"\s[{roman_regex_group}]+$"
    return series.str.replace(pattern, "", regex=True)


def clean_lis(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Cleaning LIS data such that it becomes compatible with TecDoc data...")
    df = df.copy(deep=True)
    df["category"] = clean_category_column_lis(df["category"])
    df[c.STR_COLS] = (
        df[c.STR_COLS]
        .astype("string")
        .apply(lambda x: x.str.lower())
    )
    for col in c.STR_COLS:
        df[col] = clean_whitespace(df[col])
    df["make"] = clean_make_column(df["make"])
    df["model"] = clean_model_column_lis(df["model"])
    df = clean_type_column_lis(df)
    df = clean_engine_code(df)
    logging.info("LIS data cleaned successfully.")
    return df


def clean_tecdoc(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Cleaning TecDoc data such that it becomes compatible with LIS data...")
    df["category"] = clean_category_column_tecdoc(df["category"])
    df[c.STR_COLS] = (
        df[c.STR_COLS]
        .astype("string")
        .apply(lambda x: x.str.lower())
    )
    for col in c.STR_COLS:
        df[col] = clean_whitespace(df[col])
    df["make"] = clean_make_column(df["make"])
    df = clean_model_column_tecdoc(df)
    df = clean_type_column_tecdoc(df)
    df = clean_engine_code(df)
    logging.info("TecDoc data cleaned successfully.")
    return df
