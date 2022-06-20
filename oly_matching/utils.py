import pandas as pd
import logging


def explode_column(df: pd.DataFrame, col: str, delimiter: str = ",") -> pd.DataFrame:
    n_records = len(df)
    logging.info(f"# records in df before exploding {col}: {len(df)}")
    df[col] = df[col].str.split(delimiter)
    df = df.explode(column=col)
    df[col] = (
        df[col]
        .str.replace("\s+", " ")
        .str.lstrip()
    )
    logging.info(f"Added {len(df) - n_records} records with {col}, now df has {len(df)} records")
    return df
