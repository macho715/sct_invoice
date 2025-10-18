"""
Masterfile → Warehouse 자동 동기화 엔진
CASE NO 매칭 기반 데이터 업데이트 (A~AQ열 범위 제한)
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import os
import shutil
from pathlib import Path

try:
    from .case_matcher import CaseMatcher
    from ..formatters.header_detector import HeaderDetector
    from ..validators.hvdc_validator import HVDCValidator
    from ..validators.update_tracker import UpdateTracker
    from ..formatters.header_matcher import HeaderMatcher
    from .parallel_processor import ParallelProcessor
    from ..validators.change_tracker import ChangeTracker
    from ..formatters.excel_formatter import ExcelFormatter
except ImportError:
    # 직접 실행 시 fallback
    from case_matcher import CaseMatcher
    from formatters.header_detector import HeaderDetector
    from validators.hvdc_validator import HVDCValidator
    from validators.update_tracker import UpdateTracker
    from formatters.header_matcher import HeaderMatcher
    from parallel_processor import ParallelProcessor
    from validators.change_tracker import ChangeTracker
    from formatters.excel_formatter import ExcelFormatter


class DataSynchronizer:
    """데이터 동기화 엔진 클래스"""

    def __init__(
        self,
        column_limit: str = "AG",  # Master 파일의 실제 마지막 컬럼
        backup_enabled: bool = True,
        validation_enabled: bool = True,
        prioritize_dates: bool = True,
        max_workers: int = None,
    ):
        """
        초기화

        Args:
            column_limit: 업데이트할 최대 컬럼 (기본값: 'AQ')
            backup_enabled: 백업 생성 여부
            validation_enabled: 데이터 유효성 검증 여부
            prioritize_dates: 창고별/현장별 날짜 우선순위 설정
            max_workers: 병렬 처리 최대 워커 수
        """
        self.column_limit = column_limit
        self.backup_enabled = backup_enabled
        self.validation_enabled = validation_enabled
        self.prioritize_dates = prioritize_dates

        # 컴포넌트 초기화
        self.case_matcher = CaseMatcher(max_workers=max_workers)
        self.header_detector = HeaderDetector()
        self.hvdc_validator = HVDCValidator()
        self.update_tracker = UpdateTracker()
        self.header_matcher = HeaderMatcher()
        self.parallel_processor = ParallelProcessor(max_workers)
        self.change_tracker = ChangeTracker()

        # 컬럼 제한 인덱스 계산 (AQ = 43번째 컬럼, 0-based index = 42)
        self.max_column_index = self._column_letter_to_index(column_limit)

        # 창고별/현장별 날짜 관련 키워드들 (실제 데이터 기반으로 업데이트)
        # 최우선: 창고별 날짜 컬럼들
        self.high_priority_warehouse_keywords = [
            "dhl warehouse",
            "dsv indoor",
            "dsv al markaz",
            "dsv outdoor",
            "hauler indoor",
            "dsv mzp",
            "mosb",
            "shifting",
            "mir",
            "shu",
            "das",
            "agi",
        ]

        # 중간 우선순위: 일반 날짜 컬럼들
        self.medium_priority_date_keywords = [
            "etd/atd",
            "eta/ata",
            "status_location_date",
            "etd",
            "eta",
            "atd",
            "ata",
            "arrival",
            "departure",
            "delivery",
            "shipment",
            "date",
        ]

        # 통합 키워드 리스트 (하위 호환성)
        self.warehouse_date_keywords = (
            self.high_priority_warehouse_keywords
            + self.medium_priority_date_keywords
            + ["warehouse", "site", "location", "actual", "estimated", "time"]
        )

        # 날짜 컬럼 분류
        self.date_column_patterns = [
            r".*date.*",
            r".*eta.*",
            r".*etd.*",
            r".*ata.*",
            r".*atd.*",
            r".*arrival.*",
            r".*departure.*",
            r".*delivery.*",
            r".*shipment.*",
            r".*warehouse.*",
            r".*site.*",
            r".*location.*",
        ]

        # 동기화 이력
        self.sync_history = []

    def _column_letter_to_index(self, column_letter: str) -> int:
        """
        엑셀 컬럼 문자를 인덱스로 변환 (A=0, B=1, ..., AQ=42)

        Args:
            column_letter: 컬럼 문자 (예: 'AQ')

        Returns:
            0-based 컬럼 인덱스
        """
        result = 0
        for char in column_letter.upper():
            result = result * 26 + (ord(char) - ord("A") + 1)
        return result - 1

    def _index_to_column_letter(self, index: int) -> str:
        """
        인덱스를 엑셀 컬럼 문자로 변환

        Args:
            index: 0-based 컬럼 인덱스

        Returns:
            컬럼 문자 (예: 'AQ')
        """
        result = ""
        index += 1  # 1-based로 변경
        while index > 0:
            index -= 1
            result = chr(index % 26 + ord("A")) + result
            index //= 26
        return result

    def _identify_date_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        DataFrame에서 날짜 관련 컬럼들을 식별하고 우선순위별로 분류 (실제 데이터 기반)

        Args:
            df: 대상 DataFrame

        Returns:
            우선순위별 날짜 컬럼 딕셔너리
        """
        date_columns = {
            "high_priority": [],  # 창고별/현장별 중요 날짜 (최우선)
            "medium_priority": [],  # 일반 날짜 필드
            "low_priority": [],  # 기타 시간 관련 필드
        }

        for col in df.columns:
            col_lower = str(col).lower().strip()

            # 1. 최우선: 창고별/현장별 날짜 컬럼들 (실제 데이터 기반)
            if any(
                keyword == col_lower or keyword in col_lower
                for keyword in self.high_priority_warehouse_keywords
            ):
                date_columns["high_priority"].append(col)
                print(f"[최우선] 창고별 날짜 컬럼 발견: {col}")
                continue

            # 2. 중간 우선순위: 일반 날짜 컬럼들
            if any(
                keyword == col_lower or keyword in col_lower
                for keyword in self.medium_priority_date_keywords
            ):
                date_columns["medium_priority"].append(col)
                print(f"[중간] 일반 날짜 컬럼 발견: {col}")
                continue

            # 3. 일반 날짜 패턴 매칭 (추가 탐지)
            if any(
                re.match(pattern, col_lower, re.IGNORECASE)
                for pattern in self.date_column_patterns
            ):
                if (
                    col not in date_columns["high_priority"]
                    and col not in date_columns["medium_priority"]
                ):
                    date_columns["medium_priority"].append(col)
                    print(f"[패턴매칭] 날짜 컬럼 발견: {col}")
                    continue

            # 4. 상태 관련 날짜 필드 (Status_Location_Date 등)
            if "status" in col_lower and any(
                date_word in col_lower
                for date_word in ["date", "time", "year", "month"]
            ):
                date_columns["medium_priority"].append(col)
                print(f"[상태] 날짜 컬럼 발견: {col}")
                continue

            # 5. 기타 시간 관련 필드
            if any(
                time_keyword in col_lower
                for time_keyword in ["time", "schedule", "plan", "handling"]
            ):
                if (
                    col not in date_columns["high_priority"]
                    and col not in date_columns["medium_priority"]
                ):
                    date_columns["low_priority"].append(col)

        # 발견된 날짜 컬럼 요약 출력
        print(f"\\n=== 날짜 컬럼 분류 결과 ===")
        print(
            f"최우선 ({len(date_columns['high_priority'])}개): {date_columns['high_priority']}"
        )
        print(
            f"중간 ({len(date_columns['medium_priority'])}개): {date_columns['medium_priority']}"
        )
        print(
            f"낮음 ({len(date_columns['low_priority'])}개): {date_columns['low_priority']}"
        )

        return date_columns

    def _validate_date_value(
        self, value: Any, column_name: str
    ) -> Dict[str, Any]:  # returns (summary, df) [patched]
        """
        날짜 값의 유효성 검증

        Args:
            value: 검증할 날짜 값
            column_name: 컬럼명

        Returns:
            검증 결과
        """
        validation_result = {
            "valid": True,
            "error": None,
            "warnings": [],
            "parsed_date": None,
            "original_value": value,
        }

        if pd.isna(value) or value is None or str(value).strip() == "":
            return validation_result  # 빈 값은 유효함

        value_str = str(value).strip()

        # 날짜 파싱 시도
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M",
            "%Y%m%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
        ]

        parsed_date = None
        for date_format in date_formats:
            try:
                parsed_date = pd.to_datetime(value_str, format=date_format)
                validation_result["parsed_date"] = parsed_date
                break
            except (ValueError, TypeError):
                continue

        # pandas의 일반적인 날짜 파싱 시도
        if parsed_date is None:
            try:
                parsed_date = pd.to_datetime(value_str, infer_datetime_format=True)
                validation_result["parsed_date"] = parsed_date
            except (ValueError, TypeError):
                validation_result["valid"] = False
                validation_result["error"] = (
                    f"날짜 형식을 인식할 수 없음: '{value_str}'"
                )
                return validation_result

        # 날짜 범위 검증
        if parsed_date is not None:
            current_year = datetime.now().year

            # 과거 너무 먼 날짜 (1900년 이전) 또는 미래 너무 먼 날짜 (10년 후) 경고
            if parsed_date.year < 1900:
                validation_result["warnings"].append(
                    f"매우 오래된 날짜: {parsed_date.year}년"
                )
            elif parsed_date.year > current_year + 10:
                validation_result["warnings"].append(
                    f"너무 먼 미래 날짜: {parsed_date.year}년"
                )

            # ETA/ETD 특별 검증
            if any(keyword in column_name.lower() for keyword in ["eta", "etd"]):
                if parsed_date < pd.Timestamp.now() - pd.Timedelta(days=365):
                    validation_result["warnings"].append(
                        "ETA/ETD가 1년 이상 과거 날짜임"
                    )

        return validation_result

    def _prioritize_column_mapping(
        self, column_mapping: Dict[str, str], warehouse_df: pd.DataFrame
    ) -> Dict[str, str]:
        """
        컬럼 매핑을 우선순위에 따라 정렬 (날짜 컬럼 우선)

        Args:
            column_mapping: 원본 컬럼 매핑
            warehouse_df: Warehouse DataFrame

        Returns:
            우선순위가 적용된 컬럼 매핑
        """
        if not self.prioritize_dates:
            return column_mapping

        # 날짜 컬럼 분류
        date_columns = self._identify_date_columns(warehouse_df)

        # 우선순위별로 컬럼 그룹화
        prioritized_mapping = {}

        # 1. 최우선: 창고별/현장별 날짜
        for master_col, warehouse_col in column_mapping.items():
            if warehouse_col in date_columns["high_priority"]:
                prioritized_mapping[master_col] = warehouse_col

        # 2. 중간 우선순위: 일반 날짜
        for master_col, warehouse_col in column_mapping.items():
            if (
                warehouse_col in date_columns["medium_priority"]
                and master_col not in prioritized_mapping
            ):
                prioritized_mapping[master_col] = warehouse_col

        # 3. 낮은 우선순위: 기타 시간 관련
        for master_col, warehouse_col in column_mapping.items():
            if (
                warehouse_col in date_columns["low_priority"]
                and master_col not in prioritized_mapping
            ):
                prioritized_mapping[master_col] = warehouse_col

        # 4. 나머지 컬럼들
        for master_col, warehouse_col in column_mapping.items():
            if master_col not in prioritized_mapping:
                prioritized_mapping[master_col] = warehouse_col

        return prioritized_mapping

    def _get_date_priority(
        self, column_name: str, date_columns: Dict[str, List[str]]
    ) -> str:
        """
        컬럼의 날짜 우선순위 확인

        Args:
            column_name: 확인할 컬럼명
            date_columns: 날짜 컬럼 분류 결과

        Returns:
            우선순위 ('high_priority', 'medium_priority', 'low_priority', 'non_date')
        """
        if column_name in date_columns["high_priority"]:
            return "high_priority"
        elif column_name in date_columns["medium_priority"]:
            return "medium_priority"
        elif column_name in date_columns["low_priority"]:
            return "low_priority"
        else:
            return "non_date"

    def create_backup(self, warehouse_file_path: str) -> str:
        """
        Warehouse 파일의 백업 생성

        Args:
            warehouse_file_path: 백업할 파일 경로

        Returns:
            백업 파일 경로
        """
        if not self.backup_enabled:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = Path(warehouse_file_path)
        backup_dir = file_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        # 백업 폴더 쓰기 권한 확인
        if not os.access(backup_dir, os.W_OK):
            raise PermissionError(f"백업 폴더에 쓰기 권한이 없습니다: {backup_dir}")

        backup_filename = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_filename

        shutil.copy2(warehouse_file_path, backup_path)

        return str(backup_path)

    def load_and_analyze_files(
        self, masterfile_path: str, warehouse_path: str
    ) -> Dict[str, Any]:
        """
        Masterfile과 Warehouse 파일을 로드하고 분석

        Args:
            masterfile_path: Masterfile 경로
            warehouse_path: Warehouse 파일 경로

        Returns:
            분석 결과
        """
        analysis_result = {
            "masterfile": {},
            "warehouse": {},
            "compatibility": {},
            "sync_feasibility": True,
            "issues": [],
        }

        try:
            # Masterfile 분석
            master_sheets = pd.ExcelFile(masterfile_path).sheet_names
            master_df = None
            master_sheet = None

            # CASE List가 포함된 시트 찾기
            for sheet in master_sheets:
                if "case" in sheet.lower() and "list" in sheet.lower():
                    master_sheet = sheet
                    break

            if not master_sheet and master_sheets:
                master_sheet = master_sheets[0]  # 첫 번째 시트 사용

            if master_sheet:
                # 헤더 탐지하여 로드
                df_preview = pd.read_excel(
                    masterfile_path, sheet_name=master_sheet, nrows=20, header=None
                )
                header_row = self.header_detector.detect_header_row(df_preview)

                if header_row is not None:
                    master_df = pd.read_excel(
                        masterfile_path, sheet_name=master_sheet, header=header_row
                    )
                else:
                    master_df = pd.read_excel(masterfile_path, sheet_name=master_sheet)

                analysis_result["masterfile"] = {
                    "sheet_name": master_sheet,
                    "shape": master_df.shape,
                    "columns": list(master_df.columns),
                    "header_row": header_row,
                    "case_column": self._find_case_column(master_df),
                }

            # Warehouse 파일 분석
            warehouse_sheets = pd.ExcelFile(warehouse_path).sheet_names
            warehouse_df = None
            warehouse_sheet = None

            # Case List 시트 찾기
            for sheet in warehouse_sheets:
                if "case" in sheet.lower():
                    warehouse_sheet = sheet
                    break

            if not warehouse_sheet and warehouse_sheets:
                warehouse_sheet = warehouse_sheets[0]

            if warehouse_sheet:
                # 헤더 탐지하여 로드
                df_preview = pd.read_excel(
                    warehouse_path, sheet_name=warehouse_sheet, nrows=20, header=None
                )
                header_row = self.header_detector.detect_header_row(df_preview)

                if header_row is not None:
                    warehouse_df = pd.read_excel(
                        warehouse_path, sheet_name=warehouse_sheet, header=header_row
                    )
                else:
                    warehouse_df = pd.read_excel(
                        warehouse_path, sheet_name=warehouse_sheet
                    )

                analysis_result["warehouse"] = {
                    "sheet_name": warehouse_sheet,
                    "shape": warehouse_df.shape,
                    "columns": list(warehouse_df.columns),
                    "header_row": header_row,
                    "case_column": self._find_case_column(warehouse_df),
                    "column_limit_index": min(
                        self.max_column_index, warehouse_df.shape[1] - 1
                    ),
                    "updatable_columns": list(
                        warehouse_df.columns[: self.max_column_index + 1]
                    ),
                }

            # 호환성 검사
            if master_df is not None and warehouse_df is not None:
                analysis_result["compatibility"] = self._check_compatibility(
                    master_df,
                    warehouse_df,
                    analysis_result["masterfile"]["case_column"],
                    analysis_result["warehouse"]["case_column"],
                )

                # 저장 (동기화에서 사용)
                analysis_result["masterfile"]["dataframe"] = master_df
                analysis_result["warehouse"]["dataframe"] = warehouse_df

        except Exception as e:
            analysis_result["sync_feasibility"] = False
            analysis_result["issues"].append(f"파일 분석 중 오류: {str(e)}")

        return analysis_result

    def _find_case_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        DataFrame에서 CASE NO 컬럼 찾기

        Args:
            df: 대상 DataFrame

        Returns:
            CASE NO 컬럼명 또는 None
        """
        case_keywords = ["case no", "case_no", "caseno", "case", "case number"]

        for col in df.columns:
            col_lower = str(col).lower().strip()
            for keyword in case_keywords:
                if keyword in col_lower:
                    return col

        return None

    def _check_compatibility(
        self,
        master_df: pd.DataFrame,
        warehouse_df: pd.DataFrame,
        master_case_col: str,
        warehouse_case_col: str,
    ) -> Dict[str, Any]:
        """
        두 파일 간의 호환성 검사

        Args:
            master_df: Masterfile DataFrame
            warehouse_df: Warehouse DataFrame
            master_case_col: Masterfile CASE 컬럼명
            warehouse_case_col: Warehouse CASE 컬럼명

        Returns:
            호환성 검사 결과
        """
        compatibility = {
            "case_columns_found": bool(master_case_col and warehouse_case_col),
            "common_columns": [],
            "master_only_columns": [],
            "warehouse_only_columns": [],
            "column_mapping": {},
            "issues": [],
        }

        if not compatibility["case_columns_found"]:
            compatibility["issues"].append("CASE NO 컬럼을 찾을 수 없음")
            return compatibility

        # 컬럼 비교 (업데이트 가능한 범위 내에서)
        master_columns = set(master_df.columns)
        warehouse_columns = set(warehouse_df.columns[: self.max_column_index + 1])

        compatibility["common_columns"] = list(master_columns & warehouse_columns)
        compatibility["master_only_columns"] = list(master_columns - warehouse_columns)
        compatibility["warehouse_only_columns"] = list(
            warehouse_columns - master_columns
        )

        # 컬럼 매핑 생성 (표준화된 이름 기반)
        for master_col in master_df.columns:
            master_norm = self.header_detector.standardize_column_name(master_col)

            # Warehouse에서 동일한 표준화된 이름을 가진 컬럼 찾기
            for warehouse_col in warehouse_df.columns[: self.max_column_index + 1]:
                warehouse_norm = self.header_detector.standardize_column_name(
                    warehouse_col
                )

                if master_norm == warehouse_norm:
                    compatibility["column_mapping"][master_col] = warehouse_col
                    break

        return compatibility

    def synchronize_data(
        self, masterfile_path: str, warehouse_path: str, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        데이터 동기화 실행

        Args:
            masterfile_path: Masterfile 경로
            warehouse_path: Warehouse 파일 경로
            dry_run: 실제 저장 없이 시뮬레이션만 실행

        Returns:
            동기화 결과
        """
        sync_result = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "backup_path": None,
            "analysis": {},
            "matching_results": {},
            "update_summary": {},
            "issues": [],
            "dry_run": dry_run,
        }

        try:
            # 1. 파일 분석
            analysis = self.load_and_analyze_files(masterfile_path, warehouse_path)
            sync_result["analysis"] = analysis

            if not analysis["sync_feasibility"]:
                sync_result["issues"].extend(analysis["issues"])
                return sync_result

            # 2. 백업 생성
            if not dry_run:
                backup_path = self.create_backup(warehouse_path)
                sync_result["backup_path"] = backup_path

            # 3. UpdateTracker 초기화 및 Before 상태 캡처
            warehouse_df = analysis["warehouse"]["dataframe"]
            self.update_tracker.capture_before_state(
                warehouse_df, analysis["warehouse"]["sheet_name"]
            )

            # 3. CASE NO 매칭
            master_df = analysis["masterfile"]["dataframe"]
            warehouse_df = analysis["warehouse"]["dataframe"]

            master_case_col = analysis["masterfile"]["case_column"]
            warehouse_case_col = analysis["warehouse"]["case_column"]

            if not (master_case_col and warehouse_case_col):
                sync_result["issues"].append("CASE NO 컬럼을 찾을 수 없어 동기화 불가")
                return sync_result

            matching_results = self.case_matcher.find_matching_cases(
                master_df, warehouse_df
            )
            sync_result["matching_results"] = (
                self.case_matcher.generate_matching_report(matching_results)
            )

            # 4. 컬럼 매핑 우선순위 적용 (날짜 컬럼 우선)
            prioritized_mapping = self._prioritize_column_mapping(
                analysis["compatibility"]["column_mapping"], warehouse_df
            )

            # 5. 데이터 업데이트 수행 (CASE NO 매칭 → 날짜 우선 업데이트)
            update_summary, warehouse_df = self._perform_updates(
                master_df, warehouse_df, matching_results, prioritized_mapping, dry_run
            )
            sync_result["update_summary"] = update_summary

            # 6. UpdateTracker After 상태 캡처 및 추적 종료
            self.update_tracker.capture_after_state(
                warehouse_df, analysis["warehouse"]["sheet_name"]
            )
            self.update_tracker.end_update_tracking()

            # 7. 파일 저장 (dry_run이 아닌 경우)
            if not dry_run and update_summary["total_changes"] > 0:
                # 컬럼 범위 제한 적용하여 저장
                updated_warehouse = warehouse_df.iloc[:, : self.max_column_index + 1]

                with pd.ExcelWriter(warehouse_path, engine="openpyxl") as writer:
                    updated_warehouse.to_excel(
                        writer,
                        sheet_name=analysis["warehouse"]["sheet_name"],
                        index=False,
                    )

                sync_result["success"] = True
                print(f"\n✅ 파일 저장 완료: {warehouse_path}")

                # 8. 색상 적용 (ExcelFormatter)
                print(f"🎨 변경사항 색상 표시 적용 중...")
                try:
                    formatter = ExcelFormatter(self.change_tracker)
                    success = formatter.apply_formatting_inplace(
                        excel_file_path=warehouse_path,
                        sheet_name=analysis["warehouse"]["sheet_name"],
                    )
                    if success:
                        print(f"✅ 색상 표시 완료")
                    else:
                        print(f"⚠️ 색상 표시 실패 (데이터는 정상 업데이트됨)")
                except Exception as e:
                    print(f"⚠️ 색상 표시 중 오류: {str(e)} (데이터는 정상 업데이트됨)")

            elif dry_run:
                sync_result["success"] = True  # 시뮬레이션 성공
                print(f"\n🔍 시뮬레이션 모드 완료 (실제 파일 변경 없음)")

            # 9. 상세 추적 리포트 생성
            if update_summary["total_changes"] > 0:
                print(f"\n📊 상세 추적 리포트 생성 중...")

                # 히트맵 생성
                heatmap_path = self.update_tracker.create_change_heatmap()
                sync_result["heatmap_path"] = heatmap_path

                # 상세 리포트 생성
                detailed_report_path = self.update_tracker.generate_detailed_report()
                sync_result["detailed_report_path"] = detailed_report_path

                # 비교 리포트 생성
                comparison_report = (
                    self.update_tracker.generate_change_comparison_report()
                )
                sync_result["comparison_report"] = comparison_report

            # 6. 동기화 이력 저장
            self.sync_history.append(
                {
                    "timestamp": sync_result["timestamp"],
                    "masterfile": masterfile_path,
                    "warehouse": warehouse_path,
                    "dry_run": dry_run,
                    "changes": update_summary["total_changes"],
                    "new_cases": len(matching_results.get("new_cases", [])),
                    "updated_cases": len(matching_results.get("exact_matches", {}))
                    + len(matching_results.get("fuzzy_matches", {})),
                }
            )

        except Exception as e:
            sync_result["issues"].append(f"동기화 중 오류: {str(e)}")

        return sync_result

    def _perform_updates(
        self,
        master_df: pd.DataFrame,
        warehouse_df: pd.DataFrame,
        matching_results: Dict,
        column_mapping: Dict[str, str],
        dry_run: bool,
    ) -> Tuple[Dict[str, Any], pd.DataFrame]:
        """
        실제 데이터 업데이트 수행 (병렬 처리)

        Args:
            master_df: Masterfile DataFrame
            warehouse_df: Warehouse DataFrame
            matching_results: 매칭 결과
            column_mapping: 컬럼 매핑 (이미 우선순위 적용됨)
            dry_run: 시뮬레이션 모드

        Returns:
            (업데이트 요약, 업데이트된 warehouse_df)
        """
        update_summary = {
            "updated_records": 0,
            "new_records": 0,
            "skipped_records": 0,
            "total_changes": 0,
            "updated_fields": {},
            "validation_errors": [],
            "changes_detail": [],
            "date_updates": {
                "high_priority_dates": 0,  # 창고별/현장별 날짜
                "medium_priority_dates": 0,  # 일반 날짜
                "low_priority_dates": 0,  # 기타 시간 관련
                "non_date_fields": 0,  # 날짜가 아닌 필드
            },
        }

        # 날짜 컬럼 자동 식별 (동적 헤더 매칭)
        date_columns = self.header_matcher.get_all_date_columns(warehouse_df.columns)

        # 1. 기존 레코드 업데이트 (병렬)
        all_matches = {
            **matching_results.get("exact_matches", {}),
            **matching_results.get("fuzzy_matches", {}),
        }

        if all_matches:
            update_summary, warehouse_df = self._update_existing_records_parallel(
                master_df,
                warehouse_df,
                all_matches,
                date_columns,
                dry_run,
                update_summary,
            )

        # 2. 신규 레코드 추가
        new_cases = matching_results.get("new_cases", [])
        print(f"[DEBUG] 신규 케이스 감지: {len(new_cases)}개")
        if new_cases:
            print(
                f"[DEBUG] 신규 케이스 상세: {[case.get('case_no', 'N/A') for case in new_cases[:5]]}..."
            )
            update_summary, warehouse_df = self._add_new_records_parallel(
                master_df, warehouse_df, new_cases, dry_run, update_summary
            )
        else:
            print("[DEBUG] 신규 케이스가 없습니다.")

        return update_summary, warehouse_df

    def _update_existing_records_parallel(
        self,
        master_df,
        warehouse_df,
        all_matches,
        date_columns,
        dry_run,
        update_summary,
    ):
        """기존 레코드 병렬 업데이트"""

        def update_batch(match_items):
            """배치 업데이트"""
            batch_changes = []
            batch_errors = []

            for master_idx, match_info in match_items:
                warehouse_idx = match_info["target_index"]
                master_row = master_df.iloc[master_idx]

                for col_name in warehouse_df.columns:
                    if col_name in master_row.index:
                        master_value = master_row[col_name]
                        warehouse_value = warehouse_df.at[warehouse_idx, col_name]

                        is_date = self.header_matcher.is_date_column(col_name)

                        # Master 값이 있고, 값이 다른 경우에만 업데이트
                        if pd.notna(master_value) and not self._values_equal_safe(
                            master_value, warehouse_value
                        ):
                            # 날짜 업데이트 디버그 로그
                            if is_date:
                                print(
                                    f"[DEBUG] 날짜 업데이트: {col_name} - {warehouse_value} -> {master_value}"
                                )

                            # 변경 기록
                            batch_changes.append(
                                {
                                    "wh_idx": warehouse_idx,
                                    "col_name": col_name,
                                    "new_value": master_value,
                                    "old_value": warehouse_value,
                                    "is_date": is_date,
                                    "master_idx": master_idx,
                                    "case_no": match_info.get("target_case", ""),
                                }
                            )

            return batch_changes

        # 매치된 케이스들을 배치로 나누어 병렬 처리
        match_items = list(all_matches.items())
        batch_size = max(
            100, len(match_items) // (self.parallel_processor.max_workers * 2)
        )

        # 병렬 업데이트
        change_batches = self.parallel_processor.process_batches(
            match_items, batch_size, update_batch, use_threads=True
        )

        # 변경사항 적용
        for batch in change_batches:
            for change in batch:
                if not dry_run:
                    warehouse_df.at[change["wh_idx"], change["col_name"]] = change[
                        "new_value"
                    ]

                # 변경사항 추적
                self.change_tracker.add_change(
                    case_no=change["case_no"],
                    column_name=change["col_name"],
                    old_value=change["old_value"],
                    new_value=change["new_value"],
                    change_type="date_update" if change["is_date"] else "field_update",
                    priority="master_priority",
                    row_index=change["wh_idx"],
                )

                # 통계 업데이트
                update_summary["total_changes"] += 1
                if change["is_date"]:
                    update_summary["date_updates"]["high_priority_dates"] += 1
                else:
                    update_summary["date_updates"]["non_date_fields"] += 1

        update_summary["updated_records"] = len(all_matches)
        return update_summary, warehouse_df

    def _add_new_records_parallel(
        self, master_df, warehouse_df, new_cases, dry_run, update_summary
    ):
        """신규 레코드 병렬 추가"""

        def process_new_cases_batch(cases_batch):
            """신규 케이스 배치 처리"""
            new_rows = []

            for case_info in cases_batch:
                master_idx = case_info["source_index"]
                master_row = master_df.iloc[master_idx]

                # 새 행 생성 (warehouse_df와 동일한 컬럼 구조)
                new_row = {}
                for col in warehouse_df.columns:
                    if col in master_row.index:
                        new_row[col] = master_row[col]
                    else:
                        new_row[col] = None

                new_rows.append(new_row)

                # 신규 케이스 로깅
                self.change_tracker.log_new_case(case_no=case_info["case_no"])

            return new_rows

        # 신규 케이스를 배치로 나누어 병렬 처리
        batch_size = max(
            50, len(new_cases) // (self.parallel_processor.max_workers * 2)
        )

        new_rows_batches = self.parallel_processor.process_batches(
            new_cases, batch_size, process_new_cases_batch, use_threads=True
        )

        # 신규 행들을 DataFrame에 추가 (끝에 일괄 추가)
        if not dry_run and new_rows_batches:
            # 모든 신규 행을 하나의 DataFrame으로 결합
            all_new_rows = []
            for batch in new_rows_batches:
                all_new_rows.extend(batch)

            if all_new_rows:
                new_rows_df = pd.DataFrame(all_new_rows)
                # 기존 데이터를 보존하고 끝에 추가
                warehouse_df = pd.concat(
                    [warehouse_df, new_rows_df], ignore_index=True, sort=False
                )
                print(f"[DEBUG] 신규 {len(all_new_rows)}개 행을 파일 끝에 추가 완료")

        update_summary["new_records"] = len(new_cases)
        return update_summary, warehouse_df

    def _values_equal_safe(self, val1, val2) -> bool:
        """
        안전한 값 비교 (pandas 배열 오류 방지)

        Args:
            val1: 첫 번째 값
            val2: 두 번째 값

        Returns:
            동일 여부
        """
        try:
            # pandas Series나 numpy array인 경우 첫 번째 값만 추출
            if hasattr(val1, "__len__") and not isinstance(val1, str):
                val1 = val1.iloc[0] if hasattr(val1, "iloc") else val1[0]
            if hasattr(val2, "__len__") and not isinstance(val2, str):
                val2 = val2.iloc[0] if hasattr(val2, "iloc") else val2[0]

            # NaN 체크
            val1_is_na = (
                pd.isna(val1)
                if pd.__version__ >= "1.0.0"
                else (val1 is None or str(val1).strip() == "")
            )
            val2_is_na = (
                pd.isna(val2)
                if pd.__version__ >= "1.0.0"
                else (val2 is None or str(val2).strip() == "")
            )

            if val1_is_na and val2_is_na:
                return True
            if val1_is_na or val2_is_na:
                return False

            # 문자열 비교
            return str(val1).strip() == str(val2).strip()

        except Exception:
            # 예외 발생시 문자열로 변환하여 비교
            return str(val1) == str(val2)

    def _values_equal(self, val1, val2) -> bool:
        """
        두 값이 동일한지 확인 (NaN 처리 포함)

        Args:
            val1: 첫 번째 값
            val2: 두 번째 값

        Returns:
            동일 여부
        """
        try:
            # pandas Series나 numpy array인 경우 처리
            if hasattr(val1, "__len__") and not isinstance(val1, str):
                val1 = val1.iloc[0] if hasattr(val1, "iloc") else val1[0]
            if hasattr(val2, "__len__") and not isinstance(val2, str):
                val2 = val2.iloc[0] if hasattr(val2, "iloc") else val2[0]

            # NaN 체크
            val1_is_na = (
                pd.isna(val1)
                if pd.__version__ >= "1.0.0"
                else (val1 is None or str(val1).strip() == "")
            )
            val2_is_na = (
                pd.isna(val2)
                if pd.__version__ >= "1.0.0"
                else (val2 is None or str(val2).strip() == "")
            )

            if val1_is_na and val2_is_na:
                return True
            if val1_is_na or val2_is_na:
                return False

            # 문자열 비교
            return str(val1).strip() == str(val2).strip()

        except Exception:
            # 예외 발생시 문자열로 변환하여 비교
            return str(val1) == str(val2)

    def _validate_field_update(
        self, column_name: str, new_value: Any, old_value: Any
    ) -> Dict[str, Any]:
        """
        필드 업데이트 유효성 검증

        Args:
            column_name: 컬럼명
            new_value: 새 값
            old_value: 기존 값

        Returns:
            검증 결과
        """
        validation_result = {"valid": True, "error": None, "warnings": []}

        # HVDC 코드 검증
        if "hvdc" in column_name.lower() and "code" in column_name.lower():
            if pd.notna(new_value):
                hvdc_validation = self.hvdc_validator.validate_hvdc_code(str(new_value))
                if not hvdc_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["error"] = (
                        f"HVDC 코드 형식 오류: {hvdc_validation['error']}"
                    )

        # 숫자 필드 검증
        numeric_keywords = ["cbm", "weight", "pkg", "price", "qty", "quantity"]
        if any(keyword in column_name.lower() for keyword in numeric_keywords):
            if pd.notna(new_value):
                try:
                    float_val = float(new_value)
                    if float_val < 0:
                        validation_result["warnings"].append("음수 값이 입력됨")
                except (ValueError, TypeError):
                    validation_result["valid"] = False
                    validation_result["error"] = f"숫자 형식이 아님: '{new_value}'"

        return validation_result

    def get_sync_history(self) -> List[Dict]:
        """동기화 이력 반환"""
        return self.sync_history.copy()

    def generate_sync_report(self, sync_result: Dict[str, Any]) -> str:
        """
        동기화 결과 리포트 생성

        Args:
            sync_result: 동기화 결과

        Returns:
            리포트 텍스트
        """
        report_lines = [
            "=" * 60,
            "HVDC 데이터 동기화 리포트",
            "=" * 60,
            f"실행 시간: {sync_result['timestamp']}",
            f"모드: {'시뮬레이션' if sync_result['dry_run'] else '실제 업데이트'}",
            f"상태: {'성공' if sync_result['success'] else '실패'}",
            "",
        ]

        if sync_result.get("backup_path"):
            report_lines.append(f"백업 파일: {sync_result['backup_path']}")
            report_lines.append("")

        # 매칭 결과
        if "matching_results" in sync_result:
            matching = sync_result["matching_results"]["summary"]
            report_lines.extend(
                [
                    "매칭 결과:",
                    f"  - 전체 소스 케이스: {matching['total_source_cases']}",
                    f"  - 정확한 매치: {matching['exact_matches']}",
                    f"  - 유사 매치: {matching['fuzzy_matches']}",
                    f"  - 신규 케이스: {matching['new_cases']}",
                    f"  - 모호한 매치: {matching['ambiguous_matches']}",
                    f"  - 매치율: {matching['match_rate']:.1f}%",
                    "",
                ]
            )

        # 업데이트 요약
        if "update_summary" in sync_result:
            update = sync_result["update_summary"]
            report_lines.extend(
                [
                    "업데이트 요약:",
                    f"  - 업데이트된 레코드: {update['updated_records']}",
                    f"  - 신규 레코드: {update['new_records']}",
                    f"  - 건너뛴 레코드: {update['skipped_records']}",
                    f"  - 총 변경사항: {update['total_changes']}",
                    "",
                ]
            )

            # 날짜 업데이트 세부사항
            if "date_updates" in update:
                date_stats = update["date_updates"]
                total_date_updates = (
                    date_stats["high_priority_dates"]
                    + date_stats["medium_priority_dates"]
                    + date_stats["low_priority_dates"]
                )

                if total_date_updates > 0:
                    report_lines.extend(
                        [
                            "날짜 필드 업데이트 (최우선 처리):",
                            f"  - 창고별/현장별 날짜: {date_stats['high_priority_dates']}개",
                            f"  - 일반 날짜 필드: {date_stats['medium_priority_dates']}개",
                            f"  - 기타 시간 관련: {date_stats['low_priority_dates']}개",
                            f"  - 날짜 외 필드: {date_stats['non_date_fields']}개",
                            f"  - 날짜 업데이트 비율: {(total_date_updates/max(update['total_changes'], 1)*100):.1f}%",
                            "",
                        ]
                    )

            if update["validation_errors"]:
                report_lines.extend(
                    [
                        f"검증 오류 ({len(update['validation_errors'])}건):",
                        *[
                            f"  - {error['error']}"
                            for error in update["validation_errors"][:5]
                        ],
                        "",
                    ]
                )

        # 이슈
        if sync_result.get("issues"):
            report_lines.extend(
                [
                    "발생한 이슈:",
                    *[f"  - {issue}" for issue in sync_result["issues"]],
                    "",
                ]
            )

        report_lines.append("=" * 60)

        return "\n".join(report_lines)
