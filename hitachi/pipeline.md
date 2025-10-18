# 원본 파일 위치 확인 및 전체 파이프라인 검증

## 📁 폴더 구조 이해

```
HVDC_Invoice_Audit/
├── original data/
│   └── data/              # ← 원본 파일 (절대 수정 금지)
│       ├── CASE LIST.xlsx
│       └── HVDC WAREHOUSE_HITACHI(HE).xlsx
├── pipe1/                 # ← 1차 작업: Master → Warehouse 동기화
│   ├── data_synchronizer_v29.py
│   ├── CASE LIST.xlsx (복사본)
│   └── HVDC WAREHOUSE_HITACHI(HE).xlsx (복사본 + 동기화 결과)
└── pipe2/                 # ← 2차, 3차 작업: SQM 리포트 + 이상치 탐지
    ├── hvdc_excel_reporter_final_sqm_rev (1).py
    ├── anomaly_detector/
    └── HVDC_입고로직_종합리포트_*.xlsx (결과물)
```

## 🎯 Step 1: 폴더 구조 확인

### 1.1 루트 디렉토리로 이동

```bash
cd ..
pwd
```

### 1.2 original data/data 폴더 확인

```bash
ls -la "original data/data/"
```

### 1.3 pipe1 폴더 확인

```bash
ls -la pipe1/
```

### 1.4 pipe2 폴더 확인

```bash
ls -la pipe2/
```

## 📋 Step 2: 원본 파일 상태 확인 (READ-ONLY)

### 2.1 원본 Master 파일 확인

```bash
python -c "import pandas as pd; df = pd.read_excel('original data/data/CASE LIST.xlsx'); print('Master Shape:', df.shape); print('Columns:', list(df.columns)[:5])"
```

### 2.2 원본 Warehouse 파일 확인

```bash
python -c "import pandas as pd; df = pd.read_excel('original data/data/HVDC WAREHOUSE_HITACHI(HE).xlsx'); print('Warehouse Shape:', df.shape); print('Columns:', list(df.columns)[:5])"
```

### 2.3 Master vs Warehouse 비교

```bash
python -c "
import pandas as pd
master = pd.read_excel('original data/data/CASE LIST.xlsx')
warehouse = pd.read_excel('original data/data/HVDC WAREHOUSE_HITACHI(HE).xlsx')

print('Master 행:', len(master))
print('Warehouse 행:', len(warehouse))
print('차이:', len(master) - len(warehouse))

master_cases = set(master['Case No.'].dropna())
warehouse_cases = set(warehouse['Case No.'].dropna())
print('Master 전용 Case:', len(master_cases - warehouse_cases))
print('Warehouse 전용 Case:', len(warehouse_cases - master_cases))
"
```

## 🚀 Step 3: pipe1 작업 - Master → Warehouse 동기화

### 3.1 원본 파일을 pipe1으로 복사

```bash
cp "original data/data/CASE LIST.xlsx" pipe1/
cp "original data/data/HVDC WAREHOUSE_HITACHI(HE).xlsx" pipe1/
```

### 3.2 pipe1에서 동기화 실행

```bash
cd pipe1
python data_synchronizer_v29.py
```

### 3.3 동기화 결과 확인

```bash
python -c "
import pandas as pd
df = pd.read_excel('HVDC WAREHOUSE_HITACHI(HE).xlsx')
print('동기화 후 Warehouse 행:', len(df))
print('Case NO 개수:', df['Case No.'].nunique())
"
```

### 3.4 색상 적용 확인

```bash
python -c "
import openpyxl
wb = openpyxl.load_workbook('HVDC WAREHOUSE_HITACHI(HE).xlsx')
ws = wb.active
colored_rows = 0
for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    if row[0].fill and row[0].fill.fgColor and hasattr(row[0].fill.fgColor, 'rgb'):
        colored_rows += 1
print(f'색상 적용된 행: {colored_rows}')
"
```

### 3.5 AGI 이후 컬럼 값 재계산 (원본 순서 보존) ⭐ (NEW)

**중요**: 원본 Excel의 컬럼 순서를 절대 변경하지 않고 값만 재계산

**실행**:
```bash
python calculate_agi_columns.py "HVDC WAREHOUSE_HITACHI(HE).xlsx"
```

**검증**:
```bash
python -c "
import pandas as pd
df = pd.read_excel('HVDC WAREHOUSE_HITACHI(HE).xlsx')

# AGI 이후 13개 컬럼 확인
agi_cols = ['Status_WAREHOUSE', 'Status_SITE', 'Status_Current', 'Status_Location',
            'Status_Location_Date', 'Status_Storage', 'wh handling', 'site  handling',
            'total handling', 'minus', 'final handling', 'SQM', 'Stack_Status']

print('📋 AGI 이후 컬럼 검증:')
for col in agi_cols:
    if col in df.columns:
        non_null = df[col].notna().sum()
        print(f'✅ {col}: {non_null}/{len(df)} ({non_null/len(df)*100:.1f}%)')
    else:
        print(f'❌ {col}: 컬럼 없음')

print(f'\n📊 통계:')
print(f'  - Status_Current 분포: {df[\"Status_Current\"].value_counts().to_dict()}')
print(f'  - 평균 total handling: {df[\"total handling\"].mean():.2f}')
print(f'  - 총 SQM: {df[\"SQM\"].sum():.2f}')
"
```

**컬럼 순서 검증**:
```bash
python -c "
import pandas as pd
df_before = pd.read_excel('../Data/HVDC WAREHOUSE_HITACHI(HE).xlsx')
df_after = pd.read_excel('HVDC WAREHOUSE_HITACHI(HE).xlsx')

print('원본 컬럼 수:', len(df_before.columns))
print('처리 후 컬럼 수:', len(df_after.columns))

if list(df_before.columns) == list(df_after.columns):
    print('✅ 컬럼 순서 동일 (보존됨)')
else:
    print('❌ 컬럼 순서 변경됨')
"
```

## 🚀 Step 4: pipe2 작업 - SQM 리포트 생성

### 4.1 동기화된 파일을 pipe2로 복사

```bash
cd ..
cp pipe1/HVDC\ WAREHOUSE_HITACHI\(HE\).xlsx pipe2/
```

### 4.2 pipe2에서 SQM 리포트 생성

```bash
cd pipe2
python "hvdc_excel_reporter_final_sqm_rev (1).py"
```

### 4.3 생성된 리포트 확인

```bash
ls -la HVDC_입고로직_종합리포트_*.xlsx
```

### 4.4 리포트 시트 구조 확인

```bash
python -c "
import openpyxl
import glob
files = glob.glob('HVDC_입고로직_종합리포트_*.xlsx')
if files:
    wb = openpyxl.load_workbook(files[0], read_only=True)
    print('시트 목록:', wb.sheetnames)
    if '통합_원본데이터_Fixed' in wb.sheetnames:
        print('✅ 통합_원본데이터_Fixed 시트 존재')
"
```

## 🚀 Step 5: pipe2 작업 - 이상치 탐지 및 색상 적용

### 5.1 이상치 탐지 실행

```bash
cd anomaly_detector
python anomaly_detector.py \
  --input "../HVDC_입고로직_종합리포트_*.xlsx" \
  --sheet "통합_원본데이터_Fixed" \
  --visualize \
  --no-backup
```

### 5.2 이상치 JSON 리포트 확인

```bash
ls -la anomaly_report_*.json
```

### 5.3 색상 적용 검증

```bash
python verify_colors_detailed.py
```

## 📊 Step 6: 전체 파이프라인 검증

### 6.1 각 단계별 파일 존재 확인

```bash
cd ../..
echo "=== 원본 파일 ==="
ls -la "original data/data/"
echo "=== pipe1 결과 ==="
ls -la pipe1/HVDC*.xlsx
echo "=== pipe2 결과 ==="
ls -la pipe2/HVDC*.xlsx
```

### 6.2 데이터 일관성 검증

```bash
python -c "
import pandas as pd
import glob

# pipe1 결과
df1 = pd.read_excel('pipe1/HVDC WAREHOUSE_HITACHI(HE).xlsx')
print('pipe1 (동기화 후):', len(df1), '행')

# pipe2 결과
files = glob.glob('pipe2/HVDC_입고로직_종합리포트_*.xlsx')
if files:
    df2 = pd.read_excel(files[0], sheet_name='통합_원본데이터_Fixed')
    print('pipe2 (최종 리포트):', len(df2), '행')

    # 데이터 일관성
    if len(df1) == len(df2):
        print('✅ 데이터 행 수 일치')
    else:
        print('❌ 데이터 불일치:', len(df1), 'vs', len(df2))
"
```

## 🎯 작업 흐름 요약

```
[원본] Data/
  └─ CASE LIST.xlsx
  └─ HVDC WAREHOUSE_HITACHI(HE).xlsx
         │
         │ 복사
         ↓
[1차] pipe1/
  └─ data_synchronizer_v29.py 실행
  └─ HVDC WAREHOUSE_HITACHI(HE).xlsx (동기화됨)
         │
         │ AGI 컬럼 계산 ⭐
         ↓
  └─ calculate_agi_columns.py 실행
  └─ HVDC WAREHOUSE_HITACHI(HE).xlsx (13개 컬럼 추가됨)
         │
         │ 복사
         ↓
[2차] pipe2/
  └─ hvdc_excel_reporter_final_sqm_rev (1).py 실행
  └─ HVDC_입고로직_종합리포트_*.xlsx (생성)
         │
         │ 동일 파일
         ↓
[3차] pipe2/anomaly_detector/
  └─ anomaly_detector.py --visualize 실행
  └─ 색상 적용된 최종 리포트
```

## 🚨 중요 주의사항

1. **original data/data/ 폴더는 절대 수정 금지**
2. **백업 생성 안 함 (--no-backup 사용)**
3. **각 작업은 해당 폴더에서만 수행**
4. **결과물은 작업 폴더에 저장**
5. **원본 파일은 복사해서 사용**

## ✅ 검증 체크리스트

- [ ] Data/ 원본 파일 확인
- [ ] pipe1/ 폴더에 파일 복사
- [ ] pipe1/ 에서 동기화 실행
- [ ] pipe1/ 동기화 결과 확인
- [ ] pipe1/ AGI 이후 컬럼 자동 계산 실행 ⭐
- [ ] pipe1/ 계산된 13개 컬럼 값 검증 ⭐
- [ ] pipe1/ 원본 vs 처리 후 컬럼 순서 동일성 검증 ⭐
- [ ] pipe2/ 폴더에 동기화 파일 복사
- [ ] pipe2/ 에서 SQM 리포트 생성
- [ ] pipe2/ 리포트 시트 구조 확인
- [ ] pipe2/anomaly_detector/ 에서 이상치 탐지
- [ ] pipe2/ 최종 리포트 색상 확인
- [ ] 전체 파이프라인 데이터 일관성 확인
