
import re, numpy as np, pandas as pd

def norm_port(x):
    if not isinstance(x,str): return x
    x=x.upper().strip()
    x=x.replace(" PORT","")
    x=re.sub(r"\s+"," ",x)
    return x

def apply_lane_map(df:pd.DataFrame, lane_map:pd.DataFrame|None)->pd.DataFrame:
    d=df.copy()
    if lane_map is None or lane_map.empty:
        d["origin_canon"]=d["origin"].map(norm_port)
        d["dest_canon"]=d["dest"].map(norm_port)
        return d
    lm=lane_map.copy()
    lm["OriginRaw"]=lm["OriginRaw"].astype(str).str.upper().str.strip()
    lm["DestinationRaw"]=lm["DestinationRaw"].astype(str).str.upper().str.strip()
    d["origin_u"]=d["origin"].astype(str).str.upper().str.strip()
    d["dest_u"]=d["dest"].astype(str).str.upper().str.strip()
    d=d.merge(lm[["OriginRaw","OriginCanon"]], left_on="origin_u", right_on="OriginRaw", how="left")
    d=d.merge(lm[["DestinationRaw","DestinationCanon"]], left_on="dest_u", right_on="DestinationRaw", how="left")
    d["origin_canon"]=d["OriginCanon"].fillna(d["origin_u"]).apply(norm_port)
    d["dest_canon"]=d["DestinationCanon"].fillna(d["dest_u"]).apply(norm_port)
    d=d.drop(columns=[c for c in ["origin_u","dest_u","OriginRaw","DestinationRaw","OriginCanon","DestinationCanon"] if c in d.columns])
    return d

def canon(df:pd.DataFrame, fx:dict, lane_map:pd.DataFrame|None)->pd.DataFrame:
    d=df.copy()
    for c in ["origin","dest","category","uom","currency","vendor"]:
        if c in d.columns: d[c]=d[c].astype(str).str.strip().str.upper()
    d=apply_lane_map(d, lane_map)
    if "rate" in d.columns:
        d["rate_usd"]=d.apply(lambda r: float(r["rate"])*fx.get(r["currency"],1.0), axis=1)
    d["log_qty"]=np.log1p(d.get("qty",0))
    d["log_wt"]=np.log1p(d.get("weight",0))
    d["log_cbm"]=np.log1p(d.get("volume",0))
    if "date" in d.columns:
        d["ym"]=d["date"].dt.to_period("M").astype(str)
    return d
