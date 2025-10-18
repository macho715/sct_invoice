
import argparse, json
import pandas as pd
from src.io_utils import load_config, read_table, map_columns, write_excel
from src.canon import canon
from src.rules_ref import ref_join
from src.model_reg import infer as infer_reg
from src.model_iso import score as score_iso
from src.guard import banding
from src.reporter import compose
from src.artifact import save_artifact
from src.similarity import suggest_lane

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--conf", default="config/schema.json")
    ap.add_argument("--ref", default="ref/ref_rates.csv")
    ap.add_argument("--lane", default="ref/lane_median_ewma.csv")
    ap.add_argument("--models", default="models")
    ap.add_argument("--out", default="out/costguard_report.xlsx")
    args=ap.parse_args()

    conf=load_config(args.conf)
    df=read_table(args.data)
    df=map_columns(df, conf)
    try:
        lane_map = pd.read_csv("ref/ApprovedLaneMap.csv")
    except Exception:
        lane_map = None
    df=canon(df, conf["fx"], lane_map)

    ref_rates=None; lane_median=None; unit_map=None
    try: ref_rates=read_table(args.ref)
    except Exception: pass
    try: lane_median=read_table(args.lane)
    except Exception: pass
    try: unit_map=pd.read_csv("ref/unit_map.csv")
    except Exception: unit_map=None

    df=ref_join(df, ref_rates, lane_median, unit_map)
    df=infer_reg(df, args.models)
    try:
        df=score_iso(df, f"{args.models}/iforest.joblib")
    except Exception:
        df["anomaly_score"]=0.0

    guard=conf["guard"]; bands=guard["bands"]
    df=banding(df, bands, guard["tolerance"], guard["auto_fail"])

    suggestions={}
    if lane_median is not None and not lane_median.empty:
        for idx, row in df.iterrows():
            sug = suggest_lane(row, lane_median, thr=conf.get("lane_similarity_threshold",0.60))
            if sug: suggestions[idx]=sug

    rep=compose(df)
    write_excel(rep, args.out)

    try:
        with open("out/metrics.json","r",encoding="utf-8") as f:
            metrics=json.load(f)
    except Exception:
        metrics={}

    policy = {
        "fx_locked": {"USD":1.00,"AED":1/3.6725},
        "tolerance_pct": guard["tolerance"],
        "auto_fail_pct": guard["auto_fail"],
        "bands": bands
    }
    save_artifact(rep, "out/proof_artifact.json", policy=policy, suggestions=suggestions, metrics=metrics)
    print(f"✅ saved: {args.out}")
