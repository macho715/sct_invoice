"""
CASE NO 기반 스마트 매칭 로직
대소문자, 공백, 특수문자 변형을 고려한 유연한 매칭
병렬 처리 및 동적 헤더 인식 지원
"""

import pandas as pd
import re
import unicodedata
from typing import Dict, List, Tuple, Optional, Set
from difflib import SequenceMatcher
import logging

try:
    from ..formatters.header_matcher import HeaderMatcher
    from .parallel_processor import ParallelProcessor
except ImportError:
    # 직접 실행 시 fallback
    from formatters.header_matcher import HeaderMatcher
    from parallel_processor import ParallelProcessor


class CaseMatcher:
    """CASE NO 기반 스마트 매칭 클래스"""

    def __init__(self, similarity_threshold: float = 0.95, max_workers=None):
        """
        초기화

        Args:
            similarity_threshold: 매칭 유사도 임계값 (기본값: 85%)
            max_workers: 병렬 처리 최대 워커 수
        """
        self.similarity_threshold = similarity_threshold
        self.header_matcher = HeaderMatcher()
        self.parallel_processor = ParallelProcessor(max_workers)
        self.logger = logging.getLogger(__name__)

        # CASE NO 정규화 패턴들
        self.normalization_patterns = [
            (r"\s+", ""),  # 모든 공백 제거
            (r"[-_\.]+", "-"),  # 구분자 통일
            (r"case\s*no\.?\s*:?\s*", "", re.IGNORECASE),  # "Case No:" 제거
            (r"case\s*:?\s*", "", re.IGNORECASE),  # "Case:" 제거
            (r"#", ""),  # 해시 제거
        ]

    def normalize_case_no(self, case_no: str) -> str:
        """
        CASE NO를 NFKC 정규화로 표준화

        Args:
            case_no: 원본 CASE NO

        Returns:
            정규화된 CASE NO
        """
        if pd.isna(case_no) or case_no is None:
            return ""

        # [PATCH] NFKC 정규화: 전각/반각 문자 완전 통합
        normalized = unicodedata.normalize("NFKC", str(case_no)).strip().upper()

        # 기존 정규화 패턴 적용
        for pattern, replacement, *flags in self.normalization_patterns:
            if flags:
                normalized = re.sub(pattern, replacement, normalized, flags=flags[0])
            else:
                normalized = re.sub(pattern, replacement, normalized)

        return normalized

    def calculate_similarity(self, case1: str, case2: str) -> float:
        """
        두 CASE NO 간의 유사도 계산

        Args:
            case1: 첫 번째 CASE NO
            case2: 두 번째 CASE NO

        Returns:
            유사도 (0.0 ~ 1.0)
        """
        if not case1 or not case2:
            return 0.0

        norm1 = self.normalize_case_no(case1)
        norm2 = self.normalize_case_no(case2)

        if norm1 == norm2:
            return 1.0

        # [PATCH] 기본 문자열 유사도
        base_similarity = SequenceMatcher(None, norm1, norm2).ratio()

        # 부분 매칭 가중치 (접두사/접미사 일치)
        prefix_bonus = 0.0
        suffix_bonus = 0.0

        # 공통 접두사 길이
        import os

        common_prefix_len = len(os.path.commonprefix([norm1, norm2]))
        if common_prefix_len > 3:  # 최소 3자 이상 일치
            prefix_bonus = 0.1 * (common_prefix_len / max(len(norm1), len(norm2)))

        # 공통 접미사 길이
        common_suffix_len = len(os.path.commonprefix([norm1[::-1], norm2[::-1]]))
        if common_suffix_len > 2:  # 최소 2자 이상 일치
            suffix_bonus = 0.05 * (common_suffix_len / max(len(norm1), len(norm2)))

        # 최종 유사도
        final_similarity = min(1.0, base_similarity + prefix_bonus + suffix_bonus)

        return final_similarity

    def find_matching_cases(self, master_df, warehouse_df):
        """
        소스와 타겟 간의 매칭되는 CASE NO들을 찾기 (O(n) 최적화)

        Args:
            master_df: Master DataFrame
            warehouse_df: Warehouse DataFrame

        Returns:
            매칭 결과 딕셔너리
        """
        # CASE NO 컬럼 찾기 (동적)
        master_case_col = self.header_matcher.find_column(master_df.columns, "case_no")
        warehouse_case_col = self.header_matcher.find_column(
            warehouse_df.columns, "case_no"
        )

        if not master_case_col or not warehouse_case_col:
            raise ValueError("CASE NO 컬럼을 찾을 수 없습니다")

        master_cases = master_df[master_case_col].tolist()
        warehouse_cases = warehouse_df[warehouse_case_col].tolist()

        # O(n) 딕셔너리 기반 매칭으로 최적화
        matching_results = self._match_cases_optimized(master_cases, warehouse_cases)

        return matching_results

    def _match_cases_optimized(self, master_cases, warehouse_cases):
        """
        O(n) 최적화된 매칭 알고리즘
        딕셔너리 기반 직접 매칭으로 성능 대폭 개선
        """
        matching_results = {
            "exact_matches": {},
            "fuzzy_matches": {},
            "ambiguous_matches": {},
            "new_cases": [],
        }

        # 1. Warehouse CASE NO 정규화 및 인덱스 매핑 (O(n))
        warehouse_norm_map = {}
        for idx, case in enumerate(warehouse_cases):
            norm_case = self.normalize_case_no(case)
            if norm_case not in warehouse_norm_map:
                warehouse_norm_map[norm_case] = []
            warehouse_norm_map[norm_case].append(idx)

        # 2. Master CASE NO 매칭 (O(n))
        for master_idx, master_case in enumerate(master_cases):
            norm_master = self.normalize_case_no(master_case)

            if norm_master in warehouse_norm_map:
                # 정확 매치 발견
                target_indices = warehouse_norm_map[norm_master]
                selected_idx = target_indices[0]  # 첫 번째 매치 선택

                matching_results["exact_matches"][master_idx] = {
                    "target_index": selected_idx,
                    "target_case": warehouse_cases[selected_idx],
                    "match_type": "exact",
                    "similarity": 1.0,
                }

                # 중복 CASE 로그 (요약)
                if len(target_indices) > 1:
                    self.logger.debug(
                        f"중복 CASE: {master_case} - {len(target_indices)}개 중 첫 번째 선택"
                    )
            else:
                # 정확 매치 실패 시에만 fuzzy matching 수행
                candidates = self._find_fuzzy_candidates_fast(
                    master_case, warehouse_cases, warehouse_norm_map
                )

                if candidates:
                    best_match = candidates[0]
                    candidate_case_nos = [c["target_case"] for c in candidates]

                    if len(set(candidate_case_nos)) == 1:
                        # 단일 후보
                        matching_results["fuzzy_matches"][master_idx] = best_match
                    else:
                        # 다중 후보 (모호한 매치)
                        matching_results["ambiguous_matches"][master_idx] = {
                            "source_case": master_case,
                            "candidates": candidates,
                        }
                else:
                    # 신규 케이스
                    if master_idx < 10:  # 처음 10개만 로그
                        print(f"[DEBUG] 신규 케이스 발견: {master_case}")
                    matching_results["new_cases"].append(
                        {
                            "source_index": master_idx,
                            "case_no": master_case,
                        }
                    )

        return matching_results

    def _find_fuzzy_candidates_fast(
        self, source_case, warehouse_cases, warehouse_norm_map
    ):
        """
        빠른 fuzzy 매칭 후보 찾기
        정규화된 맵을 활용하여 성능 최적화
        """
        candidates = []
        source_norm = self.normalize_case_no(source_case)

        # 정규화된 맵에서 유사한 케이스 찾기
        for norm_case, indices in warehouse_norm_map.items():
            if norm_case and source_norm:
                similarity = self.calculate_similarity(source_norm, norm_case)
                if similarity >= self.similarity_threshold:
                    for idx in indices:
                        candidates.append(
                            {
                                "target_index": idx,
                                "target_case": warehouse_cases[idx],
                                "match_type": "fuzzy",
                                "similarity": similarity,
                            }
                        )

        # 유사도 순으로 정렬
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates[:5]  # 상위 5개만 반환

    def _build_target_map_parallel(self, warehouse_cases):
        """타겟 맵 생성 (병렬)"""

        def normalize_batch(batch_with_idx):
            return [(idx, self.normalize_case_no(case)) for idx, case in batch_with_idx]

        # 인덱스와 함께 배치 생성
        indexed_cases = list(enumerate(warehouse_cases))
        batch_size = max(
            1000, len(indexed_cases) // (self.parallel_processor.max_workers * 2)
        )

        # 병렬 정규화
        normalized_batches = self.parallel_processor.process_batches(
            indexed_cases, batch_size, normalize_batch, use_threads=True
        )

        # 맵 구성
        target_map = {}
        for batch in normalized_batches:
            for idx, norm in batch:
                if norm not in target_map:
                    target_map[norm] = []
                target_map[norm].append(idx)

        return target_map

    def _match_cases_parallel(self, master_cases, warehouse_cases, target_map):
        """케이스 매칭 (병렬)"""
        matching_results = {
            "exact_matches": {},
            "fuzzy_matches": {},
            "ambiguous_matches": {},
            "new_cases": [],
        }

        def match_batch(batch_with_idx):
            batch_results = {"exact": {}, "fuzzy": {}, "ambiguous": {}, "new": []}

            for source_idx, source_case in batch_with_idx:
                source_norm = self.normalize_case_no(source_case)

                # 정확한 매치 확인
                if source_norm in target_map:
                    target_indices = target_map[source_norm]
                    selected_idx = target_indices[0]

                    batch_results["exact"][source_idx] = {
                        "target_index": selected_idx,
                        "target_case": warehouse_cases[selected_idx],
                        "match_type": "exact",
                        "similarity": 1.0,
                    }

                    if len(target_indices) > 1:
                        self.logger.info(
                            f"중복 CASE: {source_case} - "
                            f"{len(target_indices)}개 중 첫 번째 선택"
                        )
                else:
                    # Fuzzy 매칭 (기존 로직)
                    candidates = self._find_fuzzy_candidates(
                        source_case, warehouse_cases
                    )

                    if candidates:
                        best_match = candidates[0]
                        candidate_case_nos = [c["target_case"] for c in candidates]

                        if len(set(candidate_case_nos)) == 1:
                            # 중복된 동일 CASE NO
                            batch_results["fuzzy"][source_idx] = best_match
                        else:
                            # 진짜 모호한 매치
                            batch_results["ambiguous"][source_idx] = {
                                "source_case": source_case,
                                "candidates": candidates,
                            }
                    else:
                        # 신규 케이스
                        batch_results["new"].append(
                            {
                                "source_index": source_idx,
                                "case_no": source_case,
                            }
                        )

            return batch_results

        # 병렬 매칭
        indexed_cases = list(enumerate(master_cases))
        batch_size = max(
            500, len(indexed_cases) // (self.parallel_processor.max_workers * 4)
        )

        batch_results = self.parallel_processor.process_batches(
            indexed_cases, batch_size, match_batch, use_threads=True
        )

        # 결과 병합
        for result in batch_results:
            matching_results["exact_matches"].update(result["exact"])
            matching_results["fuzzy_matches"].update(result["fuzzy"])
            matching_results["ambiguous_matches"].update(result["ambiguous"])
            matching_results["new_cases"].extend(result["new"])

        # 디버그 로그
        print(
            f"[DEBUG] 매칭 결과: 정확={len(matching_results['exact_matches'])}, "
            f"유사={len(matching_results['fuzzy_matches'])}, "
            f"모호={len(matching_results['ambiguous_matches'])}, "
            f"신규={len(matching_results['new_cases'])}"
        )

        return matching_results

    def _find_fuzzy_candidates(self, source_case, warehouse_cases):
        """Fuzzy 매칭 후보 찾기"""
        source_norm = self.normalize_case_no(source_case)
        candidates = []

        for idx, target_case in enumerate(warehouse_cases):
            if pd.isna(target_case):
                continue

            similarity = self.calculate_similarity(source_norm, target_case)

            if similarity >= self.similarity_threshold:
                candidates.append(
                    {
                        "target_index": idx,
                        "target_case": target_case,
                        "similarity": similarity,
                    }
                )

        # 유사도 순으로 정렬
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates

    def resolve_ambiguous_matches(
        self, ambiguous_matches: Dict, resolution_strategy: str = "best_similarity"
    ) -> Dict:
        """
        모호한 매치들을 해결

        Args:
            ambiguous_matches: 모호한 매치 딕셔너리
            resolution_strategy: 해결 전략 ('best_similarity', 'first_match', 'manual')

        Returns:
            해결된 매치 딕셔너리
        """
        resolved_matches = {}

        for source_idx, match_info in ambiguous_matches.items():
            if resolution_strategy == "best_similarity":
                if match_info["match_type"] == "ambiguous_exact":
                    # 정확한 매치가 여러 개인 경우 첫 번째 선택
                    target_idx, target_case = match_info["candidates"][0]
                    resolved_matches[source_idx] = {
                        "target_index": target_idx,
                        "source_case": match_info["source_case"],
                        "target_case": target_case,
                        "similarity": 1.0,
                        "match_type": "exact_resolved",
                        "resolution_note": "First exact match selected from multiple candidates",
                    }
                elif match_info["match_type"] == "ambiguous_fuzzy":
                    # 유사 매치가 여러 개인 경우 가장 높은 유사도 선택
                    best_candidate = match_info["best_candidate"]
                    resolved_matches[source_idx] = {
                        **best_candidate,
                        "match_type": "fuzzy_resolved",
                        "resolution_note": "Best similarity match selected from multiple candidates",
                    }

            elif resolution_strategy == "first_match":
                # 첫 번째 후보 선택
                if match_info["candidates"]:
                    if match_info["match_type"] == "ambiguous_exact":
                        target_idx, target_case = match_info["candidates"][0]
                        similarity = 1.0
                    else:
                        candidate = match_info["candidates"][0]
                        target_idx = candidate["target_index"]
                        target_case = candidate["target_case"]
                        similarity = candidate["similarity"]

                    resolved_matches[source_idx] = {
                        "target_index": target_idx,
                        "source_case": match_info["source_case"],
                        "target_case": target_case,
                        "similarity": similarity,
                        "match_type": "first_resolved",
                        "resolution_note": "First match selected",
                    }

        return resolved_matches

    def generate_matching_report(self, matching_results: Dict) -> Dict:
        """
        매칭 결과 리포트 생성

        Args:
            matching_results: 매칭 결과

        Returns:
            매칭 리포트
        """
        total_source_cases = (
            len(matching_results["exact_matches"])
            + len(matching_results["fuzzy_matches"])
            + len(matching_results["new_cases"])
            + len(matching_results["ambiguous_matches"])
        )

        report = {
            "summary": {
                "total_source_cases": total_source_cases,
                "exact_matches": len(matching_results["exact_matches"]),
                "fuzzy_matches": len(matching_results["fuzzy_matches"]),
                "new_cases": len(matching_results["new_cases"]),
                "ambiguous_matches": len(matching_results["ambiguous_matches"]),
                "match_rate": (
                    (
                        len(matching_results["exact_matches"])
                        + len(matching_results["fuzzy_matches"])
                    )
                    / max(total_source_cases, 1)
                )
                * 100,
            },
            "details": {
                "exact_matches_sample": list(
                    matching_results["exact_matches"].values()
                )[:5],
                "fuzzy_matches_sample": list(
                    matching_results["fuzzy_matches"].values()
                )[:5],
                "new_cases_sample": matching_results["new_cases"][:5],
                "ambiguous_cases_sample": list(
                    matching_results["ambiguous_matches"].values()
                )[:3],
            },
            "recommendations": [],
        }

        # 권장사항 생성
        if report["summary"]["ambiguous_matches"] > 0:
            report["recommendations"].append(
                {
                    "type": "warning",
                    "message": f"{report['summary']['ambiguous_matches']}개의 모호한 매치가 발견됨. 수동 검토 필요.",
                }
            )

        if report["summary"]["match_rate"] < 90:
            report["recommendations"].append(
                {
                    "type": "info",
                    "message": f"매치율이 {report['summary']['match_rate']:.1f}%입니다. CASE NO 형식 표준화를 검토하세요.",
                }
            )

        if report["summary"]["new_cases"] > 0:
            report["recommendations"].append(
                {
                    "type": "info",
                    "message": f"{report['summary']['new_cases']}개의 신규 케이스가 발견됨. 추가 처리가 필요합니다.",
                }
            )

        return report

    def validate_case_format(self, case_no: str) -> Dict[str, any]:
        """
        CASE NO 형식 유효성 검증

        Args:
            case_no: 검증할 CASE NO

        Returns:
            검증 결과
        """
        if pd.isna(case_no) or not case_no:
            return {"valid": False, "error": "CASE NO가 비어있음", "suggestions": []}

        case_str = str(case_no).strip()

        # 일반적인 CASE NO 패턴들
        common_patterns = [
            r"^[A-Z0-9]+-[A-Z0-9]+-\d+$",  # ABC-DEF-123
            r"^[A-Z]{2,4}-\d{3,6}$",  # ABC-123456
            r"^\d{4}-\d{2,4}$",  # 2024-001
            r"^[A-Z]\d{3,6}$",  # A123456
        ]

        validation_result = {
            "valid": False,
            "error": "",
            "suggestions": [],
            "pattern_matched": None,
            "normalized": self.normalize_case_no(case_str),
        }

        # 패턴 매칭 확인
        for i, pattern in enumerate(common_patterns):
            if re.match(pattern, case_str.upper()):
                validation_result["valid"] = True
                validation_result["pattern_matched"] = f"Pattern_{i+1}"
                return validation_result

        # 패턴이 매치되지 않은 경우
        validation_result["error"] = "CASE NO 형식이 일반적인 패턴과 일치하지 않음"

        # 개선 제안
        if len(case_str) < 3:
            validation_result["suggestions"].append(
                "CASE NO가 너무 짧습니다. 최소 3자 이상 권장"
            )

        if not re.search(r"[A-Z0-9]", case_str.upper()):
            validation_result["suggestions"].append(
                "영문자 또는 숫자를 포함해야 합니다"
            )

        if " " in case_str:
            validation_result["suggestions"].append(
                "공백을 제거하거나 하이픈으로 대체하세요"
            )

        return validation_result
