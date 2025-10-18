
import difflib, pandas as pd

def lane_similarity(origin, dest, cand_origin, cand_dest):
    s1=difflib.SequenceMatcher(None, str(origin), str(cand_origin)).ratio()
    s2=difflib.SequenceMatcher(None, str(dest), str(cand_dest)).ratio()
    return 0.5*s1 + 0.5*s2

def suggest_lane(row, lane_table:pd.DataFrame, thr:float=0.60):
    if lane_table is None or lane_table.empty: return None
    best=None; best_s=-1.0
    for _, r in lane_table.iterrows():
        s=lane_similarity(row["origin_canon"], row["dest_canon"], r["origin_canon"], r["dest_canon"])
        if s>best_s: best, best_s = r, s
    if best_s>=thr:
        return {"candidate_lane": f"{best['category']}|{best['origin_canon']}|{best['dest_canon']}|{best['uom']}", "similarity": round(float(best_s),2)}
    return None
