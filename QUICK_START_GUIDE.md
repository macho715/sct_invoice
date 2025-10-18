# HVDC 파이프라인 빠른 시작 가이드

**5분 안에 전체 파이프라인 실행하기**

---

## 🚀 1분: 환경 준비

### Python 패키지 설치
```bash
pip install pandas openpyxl scikit-learn numpy
```

### 디렉토리 구조 확인
```bash
ls -la
# 다음 폴더들이 있어야 함:
# - pipe1/
# - pipe2/
# - hitachi/
# - Data/
```

---

## ⚡ 3분: 전체 파이프라인 실행

### 원클릭 실행 (Windows)
```bash
# 1단계: 데이터 동기화
cd pipe1
python data_synchronizer_v29.py --master "CASE LIST.xlsx" --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx"

# 2단계: Post-AGI 컬럼 계산
python post_agi_column_processor.py

# 3단계: pipe2로 복사
copy "HVDC WAREHOUSE_HITACHI(HE).xlsx" "..\pipe2\"

# 4단계: 종합 보고서 생성
cd ..\pipe2
python "hvdc_excel_reporter_final_sqm_rev (1).py"

# 5단계: 이상치 탐지 및 색상 표시
cd ..\hitachi\anomaly_detector
python anomaly_detector.py --input "..\..\pipe2\HVDC_입고로직_종합리포트_*.xlsx" --sheet "통합_원본데이터_Fixed" --visualize
```

### 원클릭 실행 (Linux/Mac)
```bash
# 1단계: 데이터 동기화
cd pipe1
python data_synchronizer_v29.py --master "CASE LIST.xlsx" --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx"

# 2단계: Post-AGI 컬럼 계산
python post_agi_column_processor.py

# 3단계: pipe2로 복사
cp "HVDC WAREHOUSE_HITACHI(HE).xlsx" "../pipe2/"

# 4단계: 종합 보고서 생성
cd ../pipe2
python "hvdc_excel_reporter_final_sqm_rev (1).py"

# 5단계: 이상치 탐지 및 색상 표시
cd ../hitachi/anomaly_detector
python anomaly_detector.py --input "../../pipe2/HVDC_입고로직_종합리포트_*.xlsx" --sheet "통합_원본데이터_Fixed" --visualize
```

---

## ✅ 1분: 결과 확인

### 최종 결과 파일 확인
```bash
# 최종 보고서 파일 확인
ls -la pipe2/HVDC_입고로직_종합리포트_*.xlsx

# 파일 크기 확인 (약 2.4MB)
dir pipe2\HVDC_입고로직_종합리포트_*.xlsx
```

### Excel에서 색상 확인
1. `pipe2/HVDC_입고로직_종합리포트_*.xlsx` 파일을 Excel로 열기
2. `통합_원본데이터_Fixed` 시트 확인
3. 색상 표시 확인:
   - 🔴 **빨간색**: 시간 역전 (397건)
   - 🟠 **주황색**: ML 이상치 높음/치명적 (115건)
   - 🟡 **노란색**: ML 이상치 보통/낮음
   - 🟣 **보라색**: 데이터 품질 (1건)

---

## 🎯 주요 결과물

### 1. 동기화된 데이터
- **파일**: `pipe1/HVDC WAREHOUSE_HITACHI(HE).xlsx`
- **내용**: Master 데이터가 반영된 Warehouse 데이터
- **색상**: 🟠 주황색 (날짜 변경), 🟡 노란색 (신규 케이스)

### 2. Post-AGI 컬럼 추가
- **파일**: `pipe1/HVDC WAREHOUSE_HITACHI(HE).xlsx`
- **추가 컬럼**: 13개 (Status_WAREHOUSE, Status_SITE, 등)
- **성능**: 벡터화 연산으로 10배 빠름

### 3. 종합 보고서
- **파일**: `pipe2/HVDC_입고로직_종합리포트_*.xlsx`
- **크기**: 약 2.4MB
- **시트**: 통합_원본데이터_Fixed, Summary, Analysis 등

### 4. 이상치 시각화
- **파일**: `pipe2/HVDC_입고로직_종합리포트_*.xlsx` (색상 표시됨)
- **탐지 건수**: 총 508건 이상치
- **백업**: `.backup_*.xlsx` 파일 자동 생성

---

## 🛠️ 문제 해결

### 자주 발생하는 오류

#### 1. 파일을 찾을 수 없음
```
FileNotFoundError: [Errno 2] No such file or directory
```
**해결방법**:
```bash
# 현재 위치 확인
pwd
# 파일 존재 확인
ls -la Data/
ls -la pipe1/
```

#### 2. Python 패키지 없음
```
ModuleNotFoundError: No module named 'pandas'
```
**해결방법**:
```bash
pip install pandas openpyxl scikit-learn numpy
```

#### 3. 메모리 부족
```
MemoryError: Unable to allocate array
```
**해결방법**:
- 다른 프로그램 종료
- 가상 메모리 증가
- 재시작 후 실행

#### 4. 색상 표시 안됨
**해결방법**:
- Excel에서 파일 열기
- `통합_원본데이터_Fixed` 시트 확인
- `--visualize` 옵션 확인

---

## 📊 성능 정보

### 처리 시간 (5,810행 기준)
- **1단계**: 5초 (데이터 동기화)
- **2단계**: 0.5초 (Post-AGI 컬럼)
- **3단계**: 0.1초 (파일 복사)
- **4단계**: 30초 (종합 보고서)
- **5단계**: 15초 (이상치 탐지)
- **총 시간**: 약 50초

### 메모리 사용량
- **최소**: 8GB RAM
- **권장**: 16GB RAM
- **최대**: 200MB (처리 중)

---

## 📚 상세 가이드

### 전체 파이프라인 가이드
- **파일**: `pipe2/PIPELINE_USER_GUIDE.md`
- **내용**: 단계별 상세 설명, 고급 사용법

### 데이터 동기화 가이드
- **파일**: `pipe1/DATA_SYNCHRONIZER_GUIDE.md`
- **내용**: 동기화 규칙, 색상 표시, 커맨드 옵션

### Post-AGI 컬럼 가이드
- **파일**: `pipe1/POST_AGI_COLUMN_GUIDE.md`
- **내용**: 13개 컬럼 상세, Excel 공식 변환

### 이상치 탐지 가이드
- **파일**: `hitachi/anomaly_detector/ANOMALY_DETECTION_GUIDE.md`
- **내용**: 탐지 알고리즘, 색상 시스템, 성능 최적화

---

## 🆘 지원

### 기술 지원
- **담당자**: AI Development Team
- **이메일**: hvdc-support@company.com

### 문제 신고
1. 오류 메시지 전체 복사
2. 실행 환경 정보 (OS, Python 버전)
3. 입력 데이터 크기
4. 로그 파일 첨부

---

**문서 끝**

생성 일시: 2025-10-18 23:10:00
파일 크기: ~8KB
총 페이지: 약 4페이지 (A4 기준)
