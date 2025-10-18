"""
HVDC Invoice Audit - Hitachi 동기화 패키지
CASE NO 매칭 기반 Excel 데이터 동기화 시스템

서브패키지 구조:
- core: 핵심 엔진 모듈 (DataSynchronizer, CaseMatcher, ParallelProcessor)
- formatters: 서식/헤더 처리 (ExcelFormatter, HeaderDetector, HeaderMatcher)
- validators: 검증/추적 (HVDCValidator, ChangeTracker, UpdateTracker)
"""

# Core modules
from .core import DataSynchronizer, CaseMatcher, ParallelProcessor

# Formatter modules
from .formatters import ExcelFormatter, HeaderDetector, HeaderMatcher

# Validator modules
from .validators import HVDCValidator, ChangeTracker, UpdateTracker

__all__ = [
    # Core modules
    "DataSynchronizer",
    "CaseMatcher",
    "ParallelProcessor",
    # Formatter modules
    "ExcelFormatter",
    "HeaderDetector",
    "HeaderMatcher",
    # Validator modules
    "HVDCValidator",
    "ChangeTracker",
    "UpdateTracker",
]

__version__ = "1.0.0"
