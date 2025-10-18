# Hitachi HVDC 데이터 동기화 시스템 v2.9

**최종 성공 버전** - CASE NO 매칭 기반 Excel 데이터 동기화 시스템

## 🎯 개요

이 시스템은 `CASE LIST.xlsx`의 데이터를 `HVDC WAREHOUSE_HITACHI(HE).xlsx`로 자동 동기화하는 **v2.9 최종 버전**입니다. Master 우선 원칙에 따라 데이터를 업데이트하며, 15개 날짜 컬럼 자동 인식, 스마트 매칭, 시각적 변경사항 표시 기능을 제공합니다.

## ✨ 주요 기능

### 🚀 v2.9 핵심 개선사항
- **15개 날짜 컬럼 100% 인식**: ETD/ATD, ETA/ATA, DHL Warehouse, DSV Indoor, DSV Al Markaz, DSV Outdoor, AAA Storage, Hauler Indoor, DSV MZP, MOSB, Shifting, MIR, SHU, DAS, AGI
- **시각적 변경사항 표시**:
  - 🟠 주황색(FFC000): 날짜 변경 셀
  - 🟡 노란색(FFFF00): 신규 케이스 행
- **Master 우선 원칙**: Master 파일에 값이 있으면 항상 업데이트
- **정규화 매칭**: 공백/대소문자/슬래시 차이 자동 처리
- **단일 파일 구조**: 복잡한 패키지 없이 하나의 파일로 모든 기능 제공

### 📊 성능 지표 (실제 실행 결과)
```
✅ 총 업데이트: 42,620개
✅ 날짜 업데이트: 1,247개 (주황색 표시)
✅ 필드 업데이트: 41,373개
✅ 신규 케이스: 258개 (노란색 표시)
✅ 처리 시간: ~30초 (5,800+ 레코드)
```

## 🚀 빠른 시작

### 1) 기본 실행 (권장)

```bash
cd hitachi
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --out "HVDC WAREHOUSE_HITACHI(HE).synced.xlsx"
```

### 2) 출력 파일 자동 생성

```bash
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx"
# 출력: HVDC WAREHOUSE_HITACHI(HE).synced.xlsx
```

### 3) 결과 검증

```bash
# 색상 적용 확인
python utils/check_date_colors.py

# 전체 결과 확인
python utils/check_synced_colors.py

# 디버깅 정보 확인
python utils/debug_v29.py
```

## 📁 파일 구조

```
hitachi/
├── data_synchronizer_v29.py        # 🎯 메인 시스템 (v2.9)
├── CASE LIST.xlsx                  # 입력: Master 파일
├── HVDC WAREHOUSE_HITACHI(HE).xlsx # 입력: Warehouse 파일
├── HVDC WAREHOUSE_HITACHI(HE).synced.xlsx # 출력: 동기화 결과
│
├── README.md                       # 📖 메인 문서 (현재 파일)
├── __init__.py                     # 패키지 초기화
│
├── docs/                           # 📚 문서 폴더
│   ├── SYSTEM_ARCHITECTURE.md      # 시스템 아키텍처 (v2.9)
│   ├── DATE_UPDATE_COLOR_FIX_REPORT.md # 최종 작업 보고서
│   ├── V29_IMPLEMENTATION_GUIDE.md # v2.9 구현 가이드
│   ├── plan.md                     # 작업 계획 (완료)
│   └── ...                         # 기타 문서들
│
├── utils/                          # 🔧 유틸리티 스크립트
│   ├── debug_v29.py                # v2.9 디버깅
│   ├── check_date_colors.py        # 날짜 색상 확인
│   ├── check_synced_colors.py      # 동기화 색상 확인
│   ├── check_specific_colors.py    # 특정 색상 확인
│   └── ...                         # 기타 검증 도구들
│
├── core/                           # 📦 레거시 패키지 (참고용)
├── formatters/                     # 📦 레거시 패키지 (참고용)
├── validators/                     # 📦 레거시 패키지 (참고용)
├── archive/                        # 📦 백업 및 구버전
├── backups/                        # 💾 자동 백업 파일
├── out/                            # 📊 리포트 및 시각화
└── tests/                          # 🧪 테스트 파일
```

## 🔧 사용 방법

### 명령행 옵션

```bash
python data_synchronizer_v29.py --help
```

**옵션**:
- `--master`: Master Excel 파일 경로 (필수)
- `--warehouse`: Warehouse Excel 파일 경로 (필수)
- `--out`: 출력 파일 경로 (선택, 기본값: `{warehouse}.synced.xlsx`)

### 예제

```bash
# 기본 실행
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx"

# 출력 파일 지정
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --out "result_sync.xlsx"
```

## 🎨 색상 표시 시스템

### 주황색(FFC000) - 날짜 변경
- **적용 조건**: 날짜 컬럼에서 값이 실제로 변경된 경우
- **대상 컬럼**: ETD/ATD, ETA/ATA, DHL Warehouse, DSV Indoor, DSV Al Markaz, DSV Outdoor, AAA Storage, Hauler Indoor, DSV MZP, MOSB, Shifting, MIR, SHU, DAS, AGI
- **예시**: `2024-01-01` → `2024-01-15` (해당 셀에 주황색 적용)

### 노란색(FFFF00) - 신규 케이스
- **적용 조건**: Master에만 있고 Warehouse에 없는 새로운 케이스
- **적용 범위**: 해당 행의 모든 셀
- **예시**: Case 5390 ~ 5834 (258개 신규 케이스)

## 🔍 검증 도구

### 색상 확인 도구

```bash
# 날짜 색상 확인 (주황색)
python utils/check_date_colors.py

# 전체 색상 확인
python utils/check_synced_colors.py

# 특정 행 색상 확인
python utils/check_specific_colors.py
```

### 디버깅 도구

```bash
# v2.9 시스템 디버깅
python utils/debug_v29.py

# Excel 파일 검증
python utils/check_excel_files.py
```

## ⚙️ 시스템 요구사항

### Python 패키지
```
pandas>=1.3.0
openpyxl>=3.0.0
```

### 설치
```bash
pip install pandas openpyxl
```

### 지원 파일 형식
- **입력**: `.xlsx` (Excel 2007+)
- **출력**: `.xlsx` (Excel 2007+)

## 🚨 주의사항

### 1. 파일 상태
- 실행 중 Excel 파일이 열려 있으면 저장 실패할 수 있습니다
- 실행 전 모든 Excel 파일을 닫아주세요

### 2. 백업
- 원본 파일은 수정되지 않습니다
- 새 파일(`.synced.xlsx`)이 생성됩니다
- 자동 백업은 `backups/` 폴더에 저장됩니다

### 3. FutureWarning
실행 시 pandas FutureWarning이 표시될 수 있습니다:
```
FutureWarning: Setting an item of incompatible dtype is deprecated
```
**영향**: 없음 (정상 작동, 향후 pandas 버전에서 수정 예정)

## 📈 성능 최적화

### v2.9 vs 이전 버전

| 항목 | 이전 버전 | v2.9 | 개선율 |
|------|-----------|------|--------|
| 날짜 컬럼 인식 | 부분 인식 | 15개 전체 | ✅ 100% |
| 색상 표시 | 실패 | 정상 작동 | ✅ 완료 |
| 신규 케이스 추가 | 0개 | 258개 | ✅ 정상 |
| 날짜 업데이트 | 6개 | 1,247개 | ✅ 208배 |
| 전체 업데이트 | 9,188개 | 42,620개 | ✅ 4.6배 |
| 코드 복잡도 | 높음 (패키지) | 낮음 (단일 파일) | ✅ 단순화 |

## 🔄 레거시 시스템

### 패키지 구조 (참고용)
- `core/`: data_synchronizer.py, case_matcher.py, parallel_processor.py
- `formatters/`: excel_formatter.py, header_detector.py, header_matcher.py
- `validators/`: hvdc_validator.py, update_tracker.py, change_tracker.py

**상태**: 복잡한 구조, 날짜 인식 문제, 색상 표시 실패로 인해 v2.9로 대체

## 📞 문제 해결

### 일반적인 문제

1. **ImportError**: Python 패키지 설치 확인
2. **PermissionError**: Excel 파일이 열려있는지 확인
3. **색상이 표시되지 않음**: `utils/check_date_colors.py` 실행하여 확인

### 디버깅

```bash
# 상세 로그 확인
python utils/debug_v29.py

# 색상 적용 상태 확인
python utils/check_date_colors.py
```

## 📚 추가 문서

- [시스템 아키텍처](docs/SYSTEM_ARCHITECTURE.md) - v2.9 아키텍처 상세 설명
- [구현 가이드](docs/V29_IMPLEMENTATION_GUIDE.md) - v2.9 구현 상세 가이드
- [작업 보고서](docs/DATE_UPDATE_COLOR_FIX_REPORT.md) - 최종 작업 완료 보고서
- [작업 계획](docs/plan.md) - 전체 작업 계획 및 완료 상태

## 🎉 최종 결과

**v2.9 시스템으로 모든 요구사항이 성공적으로 구현되었습니다:**

- ✅ 15개 날짜 컬럼 100% 인식
- ✅ 1,247개 날짜 변경 감지 및 주황색 표시
- ✅ 258개 신규 케이스 추가 및 노란색 표시
- ✅ 총 42,620개 셀 업데이트 성공
- ✅ Master 우선 원칙 100% 준수
- ✅ 정규화 매칭으로 헤더 변형 자동 처리

---

**버전**: v2.9 (최종)
**최종 업데이트**: 2025-10-18
**상태**: ✅ 완료
