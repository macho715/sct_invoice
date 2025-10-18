
# logi_costguard_ml v2 — DSV 전자료 특화 업그레이드

## What's New
1) 시간가중 레인 중앙값(EWMA) · 2) Time-aware CV(MAPE) · 3) Quantile PI(10/90)
4) 단위 변환 테이블 · 5) Lane 유사도 제안 · 6) anomaly 0–1 정규화
7) AT-COST 증빙 강화 · 8) out/metrics.json 저장

## Quick Start
pip install pandas scikit-learn joblib openpyxl
python src/build_ref_from_history_v2.py --data "data/DSV_SHPT_ALL.xlsx" --conf config/schema.json --out ref/lane_median_ewma.csv
python train.py --data "data/DSV_SHPT_ALL.xlsx" --conf config/schema.json --ref ref/ref_rates.csv --lane ref/lane_median_ewma.csv
python predict.py --data "data/new_invoice_draft.xlsx" --conf config/schema.json --ref ref/ref_rates.csv --lane ref/lane_median_ewma.csv --out out/costguard_report.xlsx
