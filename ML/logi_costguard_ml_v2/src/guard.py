
import pandas as pd, numpy as np

def banding(df:pd.DataFrame, bands:dict, tolerance:float, auto_fail:float)->pd.DataFrame:
    d=df.copy()
    d["ref_rate_usd"]=d["ref_rate_usd"].fillna(d.get("rate_ml"))
    d["delta_pct"]= (d["rate_usd"]-d["ref_rate_usd"])/d["ref_rate_usd"]*100.0
    if "rate_source" in d.columns:
        at_cost_mask = d["rate_source"].str.upper().eq("AT-COST")
        if "evidence_aed" in d.columns:
            ref_at = d.loc[at_cost_mask, "evidence_aed"] * (1/3.6725)
            d.loc[at_cost_mask, "ref_rate_usd"] = ref_at
            d.loc[at_cost_mask, "delta_pct"] = (d.loc[at_cost_mask,"rate_usd"] - ref_at) / ref_at * 100.0
    flags=[]
    flags.append(d["ref_rate_usd"].isna().map({True:"MISSING_REF", False:""}))
    flags.append(d["uom"].isna().map({True:"UNIT_MISMATCH", False:""}))
    flags.append(d["currency"].ne("USD").map({True:"CURRENCY_MISMATCH", False:""}))
    if "rate_source" in d.columns:
        need_ev = d["rate_source"].str.upper().eq("AT-COST") & d["evidence_aed"].isna()
        flags.append(need_ev.map({True:"EVIDENCE_INSUFFICIENT", False:""}))
    d["flags"]=";".join([])
    d["flags"]=pd.Series([";".join([f[i] for f in flags if f[i]]) for i in range(len(d))])
    def tier(v):
        if pd.isna(v): return "NA"
        a=abs(v)
        if a > auto_fail: return "CRITICAL"
        if a <= bands["pass"]: return "PASS"
        if a <= bands["warn"]: return "WARN"
        if a <= bands["high"]: return "HIGH"
        return "CRITICAL"
    d["band"]=d["delta_pct"].apply(tier)
    if "anomaly_score" in d.columns:
        mask = d["band"].isin(["HIGH","CRITICAL"]) & (d["anomaly_score"]<0.20)
        d.loc[mask,"band"]="WARN"
    return d
