
import json
from pathlib import Path
import pandas as pd

def save_artifact(report_df:pd.DataFrame, out_path:str, policy:dict, suggestions:dict|None=None, metrics:dict|None=None):
    payload={
        "version":"2.0",
        "policy":policy,
        "metrics": metrics or {},
        "lines":[]
    }
    for i, r in report_df.iterrows():
        item={
            "idx": int(i),
            "lane_key": f"{r.get('category','')}|{r.get('origin_canon','')}|{r.get('dest_canon','')}|{r.get('uom','')}",
            "ref_rate_usd": r.get("ref_rate_usd", None),
            "draft_rate_usd": r.get("rate_usd", None),
            "delta_pct": r.get("delta_pct", None),
            "band": r.get("band","NA"),
            "flags": r.get("flags","")
        }
        sug=(suggestions or {}).get(i)
        if sug: item["similarity_suggestion"]=sug
        payload["lines"].append(item)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path,"w",encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path
