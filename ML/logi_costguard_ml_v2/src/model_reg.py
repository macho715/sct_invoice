
from joblib import dump, load
import numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_percentage_error

CAT=["origin_canon","dest_canon","category","uom"]
NUM=["log_qty","log_wt","log_cbm"]
TARGET="rate_usd"

def build_rf():
    pre=ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
         ("num", "passthrough", NUM)],
        remainder="drop"
    )
    model=RandomForestRegressor(n_estimators=500, max_depth=14, random_state=42, n_jobs=-1)
    return Pipeline([("pre",pre),("model",model)])

def build_gb_quantile(q:float):
    pre=ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
         ("num", "passthrough", NUM)],
        remainder="drop"
    )
    model=GradientBoostingRegressor(loss="quantile", alpha=q, random_state=42)
    return Pipeline([("pre",pre),("model",model)])

def evaluate_time_aware(df:pd.DataFrame, n_splits=5):
    X=df[CAT+NUM]; y=df[TARGET]
    if "ym" in df.columns:
        groups = df["ym"].astype(str)
    else:
        groups = df["origin_canon"] + "|" + df["dest_canon"]
    gkf=GroupKFold(n_splits=min(n_splits, max(2, groups.nunique())))
    rf = build_rf()
    mape_scores=[]
    for tr, va in gkf.split(X, y, groups):
        rf.fit(X.iloc[tr], y.iloc[tr])
        pred=rf.predict(X.iloc[va])
        pred=np.clip(pred,1e-6,None)
        mape=mean_absolute_percentage_error(y.iloc[va], pred)
        mape_scores.append(mape)
    return float(np.mean(mape_scores))

def train(df:pd.DataFrame, out_dir:str):
    from pathlib import Path
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    train=df.dropna(subset=[TARGET]).copy()
    mape = evaluate_time_aware(train)
    rf = build_rf()
    rf.fit(train[CAT+NUM], train[TARGET])
    dump(rf, f"{out_dir}/rate_rf.joblib")
    gb10=build_gb_quantile(0.10); gb50=build_gb_quantile(0.50); gb90=build_gb_quantile(0.90)
    gb10.fit(train[CAT+NUM], train[TARGET]); dump(gb10, f"{out_dir}/gb_q10.joblib")
    gb50.fit(train[CAT+NUM], train[TARGET]); dump(gb50, f"{out_dir}/gb_q50.joblib")
    gb90.fit(train[CAT+NUM], train[TARGET]); dump(gb90, f"{out_dir}/gb_q90.joblib")
    return {"mape": mape}

def infer(df:pd.DataFrame, model_dir:str)->pd.DataFrame:
    from joblib import load
    rf=load(f"{model_dir}/rate_rf.joblib")
    d=df.copy()
    feats=["origin_canon","dest_canon","category","uom","log_qty","log_wt","log_cbm"]
    d["rate_ml"]=rf.predict(d[feats])
    try:
        gb10=load(f"{model_dir}/gb_q10.joblib"); gb90=load(f"{model_dir}/gb_q90.joblib")
        d["ml_p10"]=gb10.predict(d[feats]); d["ml_p90"]=gb90.predict(d[feats])
    except Exception:
        d["ml_p10"]=np.nan; d["ml_p90"]=np.nan
    return d
