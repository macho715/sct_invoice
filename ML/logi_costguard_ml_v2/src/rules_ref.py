
import pandas as pd

def apply_unit_map(df:pd.DataFrame, unit_map:pd.DataFrame)->pd.DataFrame:
    d=df.copy()
    if unit_map is None or unit_map.empty or "ref_rate_usd" not in d.columns:
        return d
    um=unit_map.copy()
    um["FromUnit"]=um["FromUnit"].astype(str).str.upper()
    um["ToUnit"]=um["ToUnit"].astype(str).str.upper()
    mask = d["uom_ref"].notna() & d["uom"].notna() & d["uom_ref"].ne(d["uom"])
    sub = d[mask]
    if not sub.empty:
        conv = sub.merge(um, left_on=["uom_ref","uom"], right_on=["FromUnit","ToUnit"], how="left")
        idx = conv["Factor"].notna()
        d.loc[conv.index[idx], "ref_rate_usd"] = conv.loc[idx, "ref_rate_usd"] * conv.loc[idx, "Factor"]
        d.loc[conv.index[idx], "uom_ref"] = conv.loc[idx, "ToUnit"]
    return d

def ref_join(df:pd.DataFrame, ref_rates:pd.DataFrame|None, lane_median:pd.DataFrame|None, unit_map:pd.DataFrame|None=None)->pd.DataFrame:
    d=df.copy()
    keys=["category","origin_canon","dest_canon","uom"]
    if ref_rates is not None and not ref_rates.empty:
        rr=ref_rates.rename(columns={"Origin":"origin_canon","Destination":"dest_canon","StdRateUSD":"ref_rate_usd"})
        rr["uom_ref"]=rr["Unit"].astype(str).str.upper()
        d=d.merge(rr[["Category","origin_canon","dest_canon","Unit","ref_rate_usd","uom_ref"]].rename(columns={"Category":"category","Unit":"uom"}),
                  on=keys, how="left")
    if lane_median is not None and not lane_median.empty:
        lm=lane_median.rename(columns={"median_rate_usd":"lm_rate_usd"})
        d=d.merge(lm[keys+["lm_rate_usd"]], on=keys, how="left")
    d["ref_rate_usd"]=d["ref_rate_usd"].fillna(d.get("lm_rate_usd"))
    d["uom_ref"]=d.get("uom_ref", d["uom"])
    d=apply_unit_map(d, unit_map)
    return d
