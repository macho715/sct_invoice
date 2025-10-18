#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""헤더 동적 인식 모듈"""

from typing import Dict, List, Optional
import re


class HeaderMatcher:
    """헤더 이름을 동적으로 인식하고 매칭"""

    def __init__(self):
        # 헤더 패턴 정의
        self.header_patterns = {
            "case_no": ["case", "no"],
            "shipment_invoice": ["shipment", "invoice"],
            "hvdc_code": ["hvdc", "code"],
            "site": ["site"],
            "eq_no": ["eq", "no", "equipment"],
            # 날짜 필드
            "dsv_indoor": ["dsv", "indoor"],
            "dsv_outdoor": ["dsv", "outdoor"],
            "mosb": ["mosb"],
            "mose": ["mose"],
            "etd": ["etd"],
            "atd": ["atd"],
            "eta": ["eta"],
            "ata": ["ata"],
            "customs_clearance": ["customs", "clearance"],
            "doc_send": ["doc", "send"],
        }

        # 날짜 키워드
        self.date_keywords = [
            "date",
            "eta",
            "etd",
            "ata",
            "atd",
            "indoor",
            "outdoor",
            "mosb",
            "mose",
            "clearance",
            "send",
            "created",
            "updated",
            "arrival",
            "departure",
            "customs",
        ]

    def normalize_header(self, header: str) -> str:
        """헤더 이름 정규화 (소문자, 특수문자 제거)"""
        if not header:
            return ""
        normalized = str(header).lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
        normalized = normalized.strip("_")
        return normalized

    def is_date_column(self, header: str) -> bool:
        """날짜 컬럼인지 확인"""
        normalized = self.normalize_header(header)
        return any(keyword in normalized for keyword in self.date_keywords)

    def get_all_date_columns(self, columns: List[str]) -> List[str]:
        """모든 날짜 컬럼 반환"""
        return [col for col in columns if self.is_date_column(col)]

    def find_column(self, columns: List[str], pattern_key: str) -> Optional[str]:
        """패턴에 맞는 컬럼 찾기"""
        keywords = self.header_patterns.get(pattern_key, [])
        for col in columns:
            normalized = self.normalize_header(col)
            if all(keyword in normalized for keyword in keywords):
                return col
        return None



