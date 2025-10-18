
import argparse, json
from pathlib import Path
import pandas as pd
from src.io_utils import load_config, read_table, map_columns
from src.canon import canon
from src.rules_ref import ref_join
from src.model_reg import train as train_reg, infer as infer_reg
from src.model_iso import fit as fit_iso

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--conf", default="config/schema.json")
    ap.add_argument("--ref", default="ref/ref_rates.csv")
    ap.add_argument("--lane", default="ref/lane_median_ewma.csv")
    ap.add_argument("--models", default="models")
    args=ap.parse_args()

    conf=load_config(args.conf)
    df=read_table(args.data)
    df=map_columns(df, conf)
    try:
        lane_map = pd.read_csv("ref/ApprovedLaneMap.csv")
    except Exception:
        lane_map = None
    df=canon(df, conf["fx"], lane_map)

    ref_rates = None; lane_median=None; unit_map=None
    try: ref_rates=read_table(args.ref)
    except Exception: pass
    try: lane_median=read_table(args.lane)
    except Exception: pass
    try: unit_map=pd.read_csv("ref/unit_map.csv")
    except Exception: unit_map=None

    df=ref_join(df, ref_rates, lane_median, unit_map)
    metrics = train_reg(df, args.models)
    pred=infer_reg(df, args.models)
    fit_iso(pred, f"{args.models}/iforest.joblib")

    Path("out").mkdir(exist_ok=True)
    with open("out/metrics.json","w",encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print("✅ training complete; metrics saved to out/metrics.json")
