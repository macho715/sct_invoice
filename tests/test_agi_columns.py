"""AGI 컬럼 정의 테스트/AGI column definition tests."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipe1.agi_columns import DERIVED_COLUMNS, SITE_HANDLING_COLUMN


def test_derived_columns_exact_match() -> None:
    """파생 컬럼명이 지정된 순서와 정확히 일치해야 한다./Derived columns must match the expected order exactly."""

    expected = [
        "Status_WAREHOUSE",
        "Status_SITE",
        "Status_Current",
        "Status_Location",
        "Status_Location_Date",
        "Status_Storage",
        "wh handling",
        "site  handling",
        "total handling",
        "minus",
        "final handling",
        "SQM",
        "Stack_Status",
    ]

    assert DERIVED_COLUMNS == expected


def test_site_handling_column_preserves_double_space() -> None:
    """site 핸들링 컬럼명에 공백 2개가 유지되어야 한다./Site handling column must keep the double space."""

    assert SITE_HANDLING_COLUMN == "site  handling"
    assert "  " in SITE_HANDLING_COLUMN
