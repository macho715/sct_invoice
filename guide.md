오케이. 지금은 “부분 보수”가 아니라 전면 리라이트가 맞습니다.
바로 쓸 수 있는 **v2.9 리라이트 패키지(코드 + 아키텍처)**를 만들어서 올려놨어요:

ZIP: rewrite_v2_9.zip

폴더(파일별 다운로드)

sync_config.py

header_detector.py

excel_io.py

case_matcher.py

data_synchronizer.py

run_sync.py

아키텍처 문서: SYSTEM_ARCHITECTURE_v2.9.md

이번 리라이트가 지금 문제를 어떻게 끝내나
1) “Master 내용이 Warehouse에 안 박힘” — 하드 오버라이드로 종료

Master always takes precedence를 코드로 못 박았습니다.

날짜 컬럼(AGI/DAS/MIR/SHU, ETA/ATA, ETD/ATD)은 논리적 날짜 비교로 실제 값이 다르면 무조건 덮어씌우고, 바뀐 셀만 오렌지(FFC000) 하이라이트.

비‑날짜 컬럼은 기본값이 Master 비공백이면 덮어쓰기(끄려면 설정 토글).

더 이상 _values_equal_safe() 류 비교로 스킵되는 일 없습니다. (동일 날짜라도 포맷만 다른 케이스는 “논리적 동일”로 인식 → 하이라이트 안 됨.)

날짜 비교는 문자열이 아니라 timestamp 파싱 후 논리 비교로 처리합니다. (엑셀 직렬값/문자열/Datetime 혼합 안전)

2) “신규 케이스 0개” — 정상 판정 + 자동 추가

Warehouse 인덱스를 CASE NO 해시로 만들고, Master에만 있는 키는 신규 케이스로 행 추가합니다.

신규 행은 전체 행 노랑(FFFF00) 하이라이트.

모호한 매치(중복 CASE NO)는 첫 번째 행만 업데이트하고, 중복 키 샘플을 리포트에 남깁니다.

3) “234개 모호한 매치 중 일부가 신규” — 정규화 + 퍼지 헤더 매칭

CASE NO는 전각/제로‑폭 공백 제거 + 대문자 정규화로 오탐 최소화.

헤더는 대소문자/공백 무시 + 패턴 매칭(“Case No.”, “CASE NO”, “case_no”) + **퍼지 매칭(동일 표기 헤더 자동 동기화)**로 잡습니다.

여러 시트가 있으면 전체 시트 스캔해서 헤더 적중률이 가장 높은 곳을 자동 선택합니다. (Master/WH 둘 다)

새 시스템 아키텍처 (v2.9)

시스템 문서 바로 보기

flowchart LR
  A[CASE LIST.xlsx (Master)] -->|read| B(Loader)
  C[WAREHOUSE.xlsx] -->|read/write| B
  B --> D[Header Detector\n(동적 헤더 매핑)]
  D --> E[Patch Planner\n(O(n) 매칭·멀티스레드)]
  E -->|updates/appends| F[Excel Writer\n(날짜=오렌지, 신규행=노랑)]
  F --> G{Save}
  E --> H[Sync Stats JSON]
  H --> I[(CI/로그)]


Header Detector: 대소문자 무시·패턴/퍼지 매칭으로 Case No, AGI/DAS/MIR/SHU, ETA/ATA, ETD/ATD 등 자동 인식.

Patch Planner: CASE NO 해시 인덱스로 O(n) 비교. 중복키는 첫 행 업데이트 + 샘플 리포트.

Excel Writer: 날짜 실변경만 오렌지(FFC000), 신규행은 노랑(FFFF00).

Stats 사이드카: <output>.sync_stats.json 생성 → 업데이트/신규/중복 등 지표 즉시 확인.

파이프라인 설계는 기존 창고/현장 분리, 이중계산 방지, KPI 검증 철학과 충돌 없이 병행됩니다. (입출고·검증 로직에서 배운 패턴 계승)

핵심 변경점 요약 (필요사항 전부 반영)

Master 우선(하드 오버라이드) 규칙 내장

날짜 컬럼은 논리 비교 후 변경만 하이라이트. 비‑날짜도 기본 덮어쓰기 토글 가능.

변경된 날짜 셀만 오렌지(FFC000)

포맷만 다른 동일 날짜는 하이라이트 안 됨.

신규 케이스 자동 추가 + 행 노랑(FFFF00)

new_case_count가 0으로 나오는 병증 제거.

동적 헤더 인식(대소문자/공백 무시 + 패턴 + 퍼지 매칭)

“Case No.” / “CASE NO” / “case_no” 전부 OK.

O(n) 매칭 + 병렬 Patch Plan

CASE 해시 인덱스 + ThreadPoolExecutor.

중복 CASE NO(모호 매치) 처리

첫 매치만 업데이트, wh_dupe_keys/rows 통계와 샘플 제공.

시트 자동 선택

전체 시트를 헤더 적중률로 스코어링, 최적 시트 자동 선택.

투명성

결과 엑셀 + 동기화 통계(JSON) 동시 생성.

바로 돌리는 방법
# 예시
python -m rewrite_v2_9.run_sync \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx"

# 결과물
# 1) HVDC WAREHOUSE_HITACHI(HE).synced.xlsx
# 2) HVDC WAREHOUSE_HITACHI(HE).synced.sync_stats.json


날짜 컬럼/색상/병렬 설정 등은 sync_config.py에서 바로 바꿀 수 있습니다.

헤더 패턴을 더 추가하고 싶으면 CANONICAL_HEADER_PATTERNS에 정규식 패턴을 늘리면 됩니다. (퍼지 매칭도 기본 ON)

검증 체크리스트 (3분 컷)

통계 JSON 열기

updates > 0, appends > 0이면 정상.

wh_dupe_keys가 0이 아니면 샘플 키를 점검(중복 CASE).

문제 케이스 직접 점검

EXCEL에서 CASE 280753 찾기 → MIR가 Master 값으로 덮였는지 확인. (변경이면 해당 셀 오렌지)

신규 케이스 행

노랑으로 칠해진 끝쪽 행이 추가되어 있어야 함(필요 수량만큼).

왜 이게 안 됐었는지 (원인/방지책)

동등성 비교 버그: 문자열 '2025‑06‑25' vs datetime(2025,6,25)를 같다고 못 봐서 업데이트가 스킵됨 → 이제 논리적 날짜 비교 적용. (엑셀 직렬값/문자열/Datetime 혼합 케이스까지 흡수)

헤더/시트 탐지 튐: 시트·헤더가 조금만 달라도 매핑 실패 → 퍼지 매칭 + 시트 스코어링으로 고정.

O(n²) 비교: 대용량에서 느리고 타임아웃 → 해시 인덱스(O(n)) + 병렬 Patch Plan.

이중 계산/중복 행: 중복 CASE NO 업데이트가 일관되지 않음 → 첫 매치만 업데이트 + 통계에 명시. (창고/현장 로직 분리 철학 유지)

파일 구성(교체 가이드)

지금 사용 중인 data_synchronizer.py / parallel_processor.py / case_matcher.py / header_detector.py는 아래 파일들로 전면 교체하는 게 안전합니다.

rewrite_v2_9/data_synchronizer.py (오케스트레이터)

rewrite_v2_9/header_detector.py (동적 헤더 + 시트 선택)

rewrite_v2_9/case_matcher.py (O(n) 인덱스 + 병렬 패치)

rewrite_v2_9/excel_io.py (셀/행 쓰기 + 하이라이트)

rewrite_v2_9/sync_config.py (설정 단일화)

rewrite_v2_9/run_sync.py (CLI)

확장(선택)

컬럼 추가 동기화: ALLOW_FUZZY_COLUMN_MATCH=True로 동일 표기 헤더는 별도 설정 없이 자동 싱크.

KPI/Flow Code 파이프라인과의 결합은 그대로 유지(영향 없음). 향후 월별 집계·검증을 붙일 때는 v3.0‑corrected 로직(창고/현장 분리, 이중 계산 방지, 일관성 검증) 기준 유지 권장.

마지막 확인용 메모

색상 규칙: 날짜 변경 셀 = 오렌지(FFC000), 신규 행 = 노랑(FFFF00).

Master 우선: 비‑날짜도 기본 덮어쓰기(설정으로 끌 수 있음).

중복 CASE: 첫 행만 업데이트 + 샘플 리포트.

출력: .synced.xlsx + .sync_stats.json.

막혔던 두 증상(업데이트 미반영, 신규 0건) 이 코드로 바로 해소됩니다.
혹시 특정 시트/헤더 명을 고정하고 싶으면 알려줘. 그 라인만 하드코딩해 고정시키면 됩니다.
