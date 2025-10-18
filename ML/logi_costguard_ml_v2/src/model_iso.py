
import numpy as np, pandas as pd
from sklearn.ensemble import IsolationForest
from joblib import dump, load

FEATS=["rate_usd","ref_rate_usd","rate_ml","log_qty","log_wt","log_cbm"]

def fit(df:pd.DataFrame, out_path:str):
    x=df[FEATS].copy().fillna(df[FEATS].median())
    iso=IsolationForest(n_estimators=400, contamination="auto", random_state=42)
    iso.fit(x)
    dump({"iso":iso,"feats":FEATS}, out_path)

def score(df:pd.DataFrame, model_path:str)->pd.DataFrame:
    payload=load(model_path); iso, feats = payload["iso"], payload["feats"]
    x=df[feats].copy().fillna(df[feats].median())
    s=-iso.score_samples(x)
    s_min, s_max = float(np.min(s)), float(np.max(s))
    s_norm = (s - s_min) / (s_max - s_min + 1e-9)
    d=df.copy(); d["anomaly_score"]=s_norm
    return d
