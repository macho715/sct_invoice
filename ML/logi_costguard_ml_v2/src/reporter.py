
import pandas as pd
ORDER={"CRITICAL":3,"HIGH":2,"WARN":1,"PASS":0,"NA":-1}
def compose(df:pd.DataFrame)->pd.DataFrame:
    keep=["date","vendor","desc","category","origin_canon","dest_canon","uom","qty","currency",
          "rate","rate_usd","ref_rate_usd","rate_ml","ml_p10","ml_p90","delta_pct","band","anomaly_score","flags"]
    rep=df[[c for c in keep if c in df.columns]].copy()
    if "band" in rep.columns:
        rep=rep.sort_values("band", key=lambda s: s.map(ORDER), ascending=False)
    return rep
