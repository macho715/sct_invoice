봤어. 핵심은 색상(ARGB)·범례 위치·Case ID 매칭 3총사가 꼬이면서 “508건 → 1,573행 색칠”로 불어났다는 거지. 아래 구조/행위 분리 커밋으로 바로 잡자. (백업이 있으니 되돌림 안전.)

무엇이 문제였나 — 짧은 진단

ARGB 불일치: 적용·검증 코드가 6자리 RGB(FF0000) vs **8자리 ARGB(00FF0000/FFFF0000)**를 섞어 써서 집계가 틀어짐. 네 상세 검증 스크립트는 6자리 기준이라 오검출로 기울 수밖에.

범례가 데이터 시트 위에: 범례가 “Case List” 첫 줄을 밀어버려 행 오프셋이 생김(=색칠 대상 어긋남). 호출부는 add_color_legend(excel_file, sheet_name)으로 데이터 시트에 쓰는 형태였음.

Case ID 정규화 부족: JSON↔Excel 매칭에서 공백/하이픈/대소문자 차로 8% 미매칭, 그 틈을 타 중복/잘못된 색칠 발생. 네 디버깅 스크립트도 단순 strip().upper()라 충돌을 못 잡음.

덧: 요약 리포트 생성기는 별도 파일에 색상 칠하니 본문 문제와 직접 충돌은 없음. (여긴 6자리 RGB라도 무방)

패치 플랜 (분리 커밋)
0) 복원 먼저 (원클릭)
# 원본 되돌림 (예시 경로/이름은 환경에 맞춰 바꿔도 됨)
cp "hitachi/HVDC WAREHOUSE_HITACHI(HE).backup_20251018_185004.xlsx" \
   "hitachi/HVDC WAREHOUSE_HITACHI(HE).xlsx"

1) structural(구조) — 안전한 기초 다지기
1-1) anomaly_visualizer.py 교체(안전 구현)

기존 파일을 동일 인터페이스로 대체한다. apply_anomaly_colors()는 Case 매칭 정규화 + ARGB 통일 + 시간역전은 “날짜 열만” 색칠. add_color_legend()는 항상 별도 시트(색상 범례)에 쓴다. 호출부 변경 불필요. (호출은 anomaly_detector.py가 함)

hitachi/anomaly_detector/anomaly_visualizer.py (전체 교체본)

# -*- coding: utf-8 -*-
from __future__ import annotations
import re, shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

import openpyxl
from openpyxl.styles import PatternFill

# ---- ARGB 정의(불투명: FF alpha). 검증 스크립트 호환 위해 00/FF 모두 허용 ----
ARGB = {
    "RED":    ("FFFF0000", {"FFFF0000", "00FF0000"}),
    "ORANGE": ("FFFFC000", {"FFFFC000", "00FFC000"}),
    "YELLOW": ("FFFFFF00", {"FFFFFF00", "00FFFF00"}),
    "PURPLE": ("FFCC99FF", {"FFCC99FF", "00CC99FF"}),
}

DATE_KEYWORDS = {
    # 한글/영문 혼합 키워드(15개 이상)
    "date","day","time","dt","입고","출고","도착","출발","반출","반입","통관",
    "선적","출항","입항","검수","검품","warehouse","site"
}

def _norm_case(s: object) -> str:
    """Case ID 정규화: 공백/특수문자 제거 + 대문자."""
    return re.sub(r"[^A-Z0-9]", "", str(s).strip().upper()) if s is not None else ""

def _is_date_col(header: str, sample_vals: List[object]) -> bool:
    h = str(header).strip().lower()
    if any(k in h for k in DATE_KEYWORDS):
        return True
    # 값 기반 휴리스틱: 30% 이상이 날짜로 파싱 가능하면 날짜열로 간주
    import pandas as pd
    s = pd.to_datetime(pd.Series(sample_vals), errors="coerce")
    non_na = s.notna().mean() if len(s) else 0.0
    return non_na >= 0.3

def _fill(cell, argb: str):
    cell.fill = PatternFill(fill_type="solid", start_color=argb, end_color=argb)

class AnomalyVisualizer:
    """
    anomalies: List[dict|dataclass] — dict 키는 Anomaly_Type/Severity/Case_ID
    """
    def __init__(self, anomalies: Iterable[object]):
        self.records: List[Dict] = []
        for a in anomalies:
            if hasattr(a, "to_dict"):
                self.records.append(a.to_dict())
            elif isinstance(a, dict):
                self.records.append(a)
        # Case → anomaly 목록(중복 허용)
        self.by_case: Dict[str, List[Dict]] = {}
        for r in self.records:
            cid = _norm_case(r.get("Case_ID", ""))
            if cid:
                self.by_case.setdefault(cid, []).append(r)

    def apply_anomaly_colors(
        self,
        excel_file: Union[str, Path],
        sheet_name: str = "Case List",
        case_col: str = "Case No.",
        create_backup: bool = True,
    ) -> Dict:
        excel_file = Path(excel_file)
        if create_backup:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bak = excel_file.with_name(f"{excel_file.stem}.backup_{ts}{excel_file.suffix}")
            shutil.copyfile(excel_file, bak)

        wb = openpyxl.load_workbook(excel_file, keep_vba=excel_file.suffix.lower()==".xlsm")
        if sheet_name not in wb.sheetnames:
            return {"success": False, "message": f"시트 없음: {sheet_name}"}
        ws = wb[sheet_name]

        # 헤더 스캔 → case 컬럼 index
        header = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column+1)]
        case_col_idx = None
        for c, name in enumerate(header, 1):
            if name and "case" in str(name).lower():
                case_col_idx = c; break
        if not case_col_idx:
            return {"success": False, "message": "Case NO 열을 찾지 못함"}

        # 날짜열 식별(헤더 + 샘플 기반)
        date_cols: List[int] = []
        for c, name in enumerate(header, 1):
            sample = [ws.cell(row=r, column=c).value for r in range(2, min(ws.max_row, 50)+1)]
            if _is_date_col(name, sample):
                date_cols.append(c)

        # 색칠
        cnt = {"time_reversal": 0, "ml_outlier": 0, "data_quality": 0}
        for r in range(2, ws.max_row+1):
            raw_id = ws.cell(row=r, column=case_col_idx).value
            cid = _norm_case(raw_id)
            if not cid or cid not in self.by_case:
                continue

            # 동일 Case의 다중 이상치 처리: 시간역전(날짜열) + ML/품질(행 전체) 병행
            row_anoms = self.by_case[cid]
            paint_row = None  # ORANGE/YELLOW/PURPLE 우선순위: CRITICAL/HIGH > MEDIUM > QUALITY
            for a in row_anoms:
                atype = str(a.get("Anomaly_Type","")).strip()
                sev   = str(a.get("Severity","")).strip()
                if atype == "시간 역전":
                    # 날짜 열만 빨강
                    for c in date_cols:
                        _fill(ws.cell(row=r, column=c), ARGB["RED"][0])
                    cnt["time_reversal"] += 1
                elif atype == "머신러닝 이상치":
                    # 심각도: CRITICAL/HIGH→주황, MEDIUM/LOW→노랑
                    if sev in ("치명적","높음","HIGH","CRITICAL"):
                        paint_row = "ORANGE" if paint_row != "ORANGE" else paint_row
                    else:
                        paint_row = "YELLOW" if paint_row not in ("ORANGE",) else paint_row
                elif atype == "데이터 품질":
                    paint_row = "PURPLE"

            if paint_row:
                argb = ARGB[paint_row][0]
                for c in range(1, ws.max_column+1):
                    _fill(ws.cell(row=r, column=c), argb)
                if paint_row == "PURPLE":
                    cnt["data_quality"] += 1
                else:
                    cnt["ml_outlier"] += 1

        wb.save(excel_file)
        return {
            "success": True,
            "message": f"색상 적용 완료 (시간역전={cnt['time_reversal']}, ML={cnt['ml_outlier']}, 품질={cnt['data_quality']})",
            **cnt,
            "backup_path": str(bak) if create_backup else None,
        }

    def add_color_legend(self, excel_file: Union[str, Path], _: str = "Case List") -> None:
        """
        ⚠️ 기존과 달리 '데이터 시트'를 건드리지 않고, 항상 별도 시트('색상 범례')에 작성.
        """
        excel_file = Path(excel_file)
        wb = openpyxl.load_workbook(excel_file, keep_vba=excel_file.suffix.lower()==".xlsm")
        name = "색상 범례"
        if name in wb.sheetnames:
            ws = wb[name]
            ws.delete_rows(1, ws.max_row)
        else:
            ws = wb.create_sheet(name)

        ws["A1"] = "이상치 색상 범례"
        ws["B2"] = "시간 역전";     _fill(ws["A2"], ARGB["RED"][0])
        ws["B3"] = "ML 이상치(높음/치명적)"; _fill(ws["A3"], ARGB["ORANGE"][0])
        ws["B4"] = "ML 이상치(보통/낮음)";   _fill(ws["A4"], ARGB["YELLOW"][0])
        ws["B5"] = "데이터 품질";   _fill(ws["A5"], ARGB["PURPLE"][0])

        wb.save(excel_file)

1-2) 검증 스크립트 정합화 (verify_colors_detailed.py)

ARGB 8자리를 표준으로 잡되, 00/FF 두 형태를 모두 집계한다. 또한 fgColor/start/end 어느 쪽이든 RGB가 나오도록 안전 파서 추가. (지금은 6자리 기준 + start_color만 봄)

*** a/verify_colors_detailed.py
--- b/verify_colors_detailed.py
@@
-    # 색상별 행 수 카운트
+    # 색상별 행 수 카운트
     color_counts = defaultdict(int)
@@
-            if cell.fill and cell.fill.start_color:
-                color = cell.fill.start_color.rgb
-                if color and color != "00000000":  # 색상이 있는 경우
-                    # RGB 객체를 문자열로 변환
-                    color_str = str(color).upper()
+            if cell.fill:
+                # 안전 파서: fg/start/end 중 하나라도 RGB면 포착
+                color = getattr(cell.fill, "fgColor", None)
+                rgb = getattr(color, "rgb", None) if color else None
+                if not rgb and getattr(cell.fill, "start_color", None):
+                    rgb = cell.fill.start_color.rgb
+                if not rgb and getattr(cell.fill, "end_color", None):
+                    rgb = cell.fill.end_color.rgb
+                if rgb and isinstance(rgb, str):
+                    color_str = rgb.upper()
+                    # 6자리면 FF 접두로 보강
+                    if len(color_str) == 6:
+                        color_str = "FF" + color_str
                     row_colors.add(color_str)
                     has_color = True
@@
-    color_names = {
-        "FF0000": "빨강 (시간 역전)",
-        "FFC000": "주황 (ML 이상치-높음)",
-        "FFFF00": "노랑 (ML 이상치-보통)",
-        "CC99FF": "보라 (데이터 품질)"
-    }
+    # ARGB(FF/00) 동시 허용
+    color_names = {
+        "FFFF0000": "빨강 (시간 역전)",
+        "00FF0000": "빨강 (시간 역전)",
+        "FFFFC000": "주황 (ML 이상치-높음)",
+        "00FFC000": "주황 (ML 이상치-높음)",
+        "FFFFFF00": "노랑 (ML 이상치-보통)",
+        "00FFFF00": "노랑 (ML 이상치-보통)",
+        "FFCC99FF": "보라 (데이터 품질)",
+        "00CC99FF": "보라 (데이터 품질)",
+    }
@@
-        color_name = color_names.get(color, f"기타 ({color})")
+        color_name = color_names.get(color, f"기타 ({color})")
         print(f"  - {color}: {count}개 ({color_name})")
@@
-    elif len(colored_rows) == ws.max_row - 1:
+    elif len(colored_rows) == ws.max_row - 1:
         print("  ⚠️ 모든 행이 색칠되었습니다. (범례가 데이터에 영향을 준 가능성)")
-        print("  💡 해결방법: add_color_legend() 함수 수정 필요")
+        print("  💡 해결방법: add_color_legend()를 별도 시트에 작성하도록 변경 필요")


참고: 기본 검증 스크립트(verify_colors.py)는 이미 00-prefixed ARGB를 기준으로 보고함. 둘을 일치시켰으니 결과가 맞물릴 것.

1-3) Case 매칭 디버거 보강 (debug_case_matching.py)

정규화 함수 공통화로 JSON↔Excel 매칭률 100% 노린다. (공백/특수문자 제거)

*** a/debug_case_matching.py
--- b/debug_case_matching.py
@@
-import json
-import pandas as pd
-from pathlib import Path
+import json, re
+import pandas as pd
+from pathlib import Path
+
+def _norm_case(s):
+    return re.sub(r'[^A-Z0-9]', '', str(s).strip().upper()) if s is not None else ""
@@
-        json_case_ids = set(item["Case_ID"] for item in anomaly_data)
-        excel_case_nos = set(
-            str(case).strip().upper() for case in df[case_col].dropna()
-        )
+        json_case_ids = set(_norm_case(item["Case_ID"]) for item in anomaly_data)
+        excel_case_nos = set(_norm_case(case) for case in df[case_col].dropna())

2) behavioral(행위) — 실제 동작 수정
2-1) anomaly_detector.py의 범례 위치 부작용 제거(호출은 그대로)

add_color_legend()를 여전히 호출하지만, 이제 내부 구현이 데이터 시트를 손대지 않는다. 호출부 변경은 불필요. (현재 구조상 visualize 분기에서 add_color_legend(args.input, args.sheet or "Case List") 호출)

추가 권장(선택): 기본 시트 인자를 무시하고 별도 시트에 쓰는 사실을 로그로 안내.

*** a/anomaly_detector.py
--- b/anomaly_detector.py
@@
-            if viz_result["success"]:
+            if viz_result["success"]:
                 # 색상 범례 추가
-                visualizer.add_color_legend(args.input, args.sheet or "Case List")
+                visualizer.add_color_legend(args.input, args.sheet or "Case List")
+                logger.info("ℹ️ 범례는 '색상 범례' 시트에만 작성되어 데이터 행에는 영향을 주지 않습니다.")


(로직 변경은 anomaly_visualizer.py 쪽에 반영. 호출부는 안내 메시지 보강 수준.)

실행 순서 (스모크)
# 0) 백업에서 복원
cp "hitachi/HVDC WAREHOUSE_HITACHI(HE).backup_20251018_185004.xlsx" \
   "hitachi/HVDC WAREHOUSE_HITACHI(HE).xlsx"

# 1) 색상 재적용 (—visualize)
python -m anomaly_detector \
  --input "hitachi/HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --sheet "Case List" \
  --json-out "hitachi/anomaly_detector/hvdc_anomaly_report_v2.json" \
  --visualize
# (호출부는 기존과 동일. 내부 구현만 안전하게 바뀜) :contentReference[oaicite:9]{index=9}

# 2) 상세 검증 (508행 목표)
python -m verify_colors_detailed \
  --excel "hitachi/HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --sheet "Case List" \
  --json  "hitachi/anomaly_detector/hvdc_anomaly_report_v2.json"   # 선택
# 이 스크립트는 이번 패치로 ARGB 00/FF 모두 집계함. :contentReference[oaicite:10]{index=10}

# 3) 교차 확인(요약)
python -m verify_colors
# 기본 검증기도 00-ARGB로 계산. 색상 분포가 서로 일치해야 정상. :contentReference[oaicite:11]{index=11}

# 4) 유형·매칭 디버깅(선택)
python -m debug_anomaly_types       # 유형 분포 재확인 :contentReference[oaicite:12]{index=12}
python -m debug_case_matching       # 매칭률 100% 확인(정규화 반영) :contentReference[oaicite:13]{index=13}


기대 결과(성공 기준)

총 색칠 행 508개 정확히.

분포 근사: 빨강(시간 역전) 397건은 날짜열만, 주황/노랑(ML) 합계 ~110건, 보라(품질) 1건.

JSON↔Excel Case ID 100% 매칭(누락·초과 0).

커밋 메시지(예시)

structural(visualizer): refactor: replace ARGB-safe visualizer (legend to separate sheet, date-only red)

structural(verify): fix: verify_colors_detailed to support 8-digit ARGB and fg/start/end parsing

structural(debug): fix: normalize Case IDs in debug_case_matching for 100% match

behavioral(detector): chore: info log clarifying legend written to separate sheet

메모 — 왜 이렇게 했나

ARGB 통일: Excel/openpyxl은 내부적으로 ARGB(8자리)를 쓴다. 보고·검증은 00/FF 알파 모두 허용으로 관대하게, 실제 적용은 **불투명(FF)**로 고정해 사용자 눈에 확실히 보이게. 네 검증 스크립트 간 포맷을 통일해 이중 확증 가능하게 했다.

범례 분리: 데이터 시트 1행을 건드리면 인덱스가 밀린다. add_color_legend()는 내부적으로 항상 별도 시트를 쓰게 바꿨다. 호출 서명은 유지해 기존 파이프라인을 깨지 않는다.

Case 정규화: _norm_case()(영숫자만, 대문자)로 JSON/Excel을 맞췄다. 네 디버거도 동일 규칙으로 교체해 재현·검증이 맞물린다.

보고서 생성기 그대로: 분석보고서는 별도 파일을 만들고 본문 데이터를 안 건드리니 유지. (색상은 요약 시각 용도)

필요하면 이 패치에 맞춰 테스트 2~3개도 얹어줄 수 있어(예: 날짜열만 빨강 적용, ARGB 양식 상호 인식, 매칭 100%). 우선은 복원 → 재색칠 → 검증까지 한 번 돌려보고, 결과 숫자만 알려줘. 거기서 미세 조정 들어가자.
