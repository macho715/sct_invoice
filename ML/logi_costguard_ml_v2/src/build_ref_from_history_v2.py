
import argparse, pandas as pd, numpy as np
from pathlib import Path
from io_utils import load_config, read_table, map_columns
from canon import canon

def ewma_by_month(series, alpha=0.85):
    vals=series.values
    if len(vals)==0: return np.nan
    s=None
    for v in vals:
        s = v if s is None else alpha*v + (1-alpha)*s
    return s

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--conf", required=True)
    ap.add_argument("--out", required=True)
    args=ap.parse_args()

    conf=load_config(args.conf)
    df=read_table(args.data)
    df=map_columns(df, conf)
    df=canon(df, conf["fx"], lane_map=None)

    if "ym" not in df.columns:
        raise SystemExit("date/ym not available in data. Provide date column.")

    grp = (df
        .groupby(["category","origin_canon","dest_canon","uom","ym"])["rate_usd"]
        .median()
        .reset_index())

    out_rows=[]
    for key, sub in grp.groupby(["category","origin_canon","dest_canon","uom"], as_index=False):
        sub = sub.sort_values("ym")
        ew = ewma_by_month(sub["rate_usd"], alpha=0.85)
        row=dict(zip(["category","origin_canon","dest_canon","uom"], key))
        row["median_rate_usd"]=ew
        out_rows.append(row)
    out = pd.DataFrame(out_rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"✅ lane median (EWMA) saved: {args.out} ({len(out)} lanes)")
