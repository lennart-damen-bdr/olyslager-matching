import pandas as pd


def explode_column(df: pd.DataFrame, col: str, delimiter: str = ",") -> pd.DataFrame:
    n_records = len(df)
    print(f"# records in df before exploding {col}: {len(df)}")
    df[col] = df[col].str.split(delimiter)
    df = df.explode(column=col)
    df[col] = (
        df[col]
        .str.replace("\s+", " ")
        .str.lstrip()
    )
    print(f"Added {len(df) - n_records} records with {col}, now df has {len(df)} records")
    return df


def roman_to_int(s: str) -> int:
    roman = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000,'IV':4,'IX':9,'XL':40,'XC':90,'CD':400,'CM':900}
    for k, v in roman.copy().items():
        roman[k.lower()] = v
    i = 0
    num = 0
    while i < len(s):
        if i + 1 < len(s) and s[i:i+2] in roman:
            num += roman[s[i:i+2]]
            i += 2
        else:
            num += roman[s[i]]
            i += 1
    return num
