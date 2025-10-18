
import json, re
import pandas as pd
from pathlib import Path

def load_config(p:str)->dict:
    with open(p,"r",encoding="utf-8") as f:
        return json.load(f)

def read_table(path:str)->pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in [".xlsx",".xls"]:
        return pd.read_excel(p)
    return pd.read_csv(p)

def pick(df:pd.DataFrame, cands:list[str]):
    for c in cands:
        if c in df.columns: return c
    return None

def map_columns(df:pd.DataFrame, conf:dict)->pd.DataFrame:
    cols=conf["cols"]; ren={}
    for k,cands in cols.items():
        col=pick(df, cands)
        if col: ren[col]=k
    out=df.rename(columns=ren).copy()
    req=["origin","dest","uom","currency"]
    miss=[r for r in req if r not in out.columns]
    if miss: raise ValueError(f"필수 컬럼 누락: {miss}")
    if "date" in out.columns:
        out["date"]=pd.to_datetime(out["date"], errors="coerce")
    return out

def write_excel(df:pd.DataFrame, path:str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)
