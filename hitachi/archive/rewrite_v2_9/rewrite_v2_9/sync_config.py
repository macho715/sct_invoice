"""
Sync configuration for Master→Warehouse Excel synchronization (v2.9 rewrite).

- Canonical column names and dynamic header matching
- Date columns and highlight colors
- Concurrency & batch configs
"""

from dataclasses import dataclass, field
from typing import Dict, List, Pattern, Set
import re
import os

# === Canonical columns we care about ===
# You can extend this list as needed. Keys are canonical, values are regex patterns to match header cells.
CANONICAL_HEADER_PATTERNS: Dict[str, List[Pattern]] = {
    # Tier 1 - 필수 식별 및 날짜 컬럼
    "case_no": [
        re.compile(r"^case\s*no\.?$", re.I),
        re.compile(r"^case[_\s-]*no$", re.I),
        re.compile(r"^sku$", re.I),
        re.compile(r"^case$", re.I),
    ],
    "agi": [re.compile(r"^agi$", re.I), re.compile(r"^agi\s*date$", re.I)],
    "das": [re.compile(r"^das$", re.I), re.compile(r"^das\s*date$", re.I)],
    "mir": [re.compile(r"^mir$", re.I), re.compile(r"^mir\s*date$", re.I)],
    "shu": [re.compile(r"^shu$", re.I), re.compile(r"^shu\s*date$", re.I)],
    "eta_ata": [re.compile(r"^eta/ata$", re.I), re.compile(r"^eta\s*/\s*ata$", re.I)],
    "etd_atd": [re.compile(r"^etd/atd$", re.I), re.compile(r"^etd\s*/\s*atd$", re.I)],
    # Tier 2 - 물류 핵심 정보
    "vessel": [
        re.compile(r"^vessel$", re.I),
        re.compile(r"^vessel\s*name$", re.I),
        re.compile(r"^ship\s*name$", re.I),
    ],
    "pol": [
        re.compile(r"^pol$", re.I),
        re.compile(r"^port\s*of\s*loading$", re.I),
        re.compile(r"^loading\s*port$", re.I),
    ],
    "pod": [
        re.compile(r"^pod$", re.I),
        re.compile(r"^port\s*of\s*discharge$", re.I),
        re.compile(r"^discharge\s*port$", re.I),
    ],
    "coe": [re.compile(r"^coe$", re.I), re.compile(r"^country\s*of\s*export$", re.I)],
    "hs_code": [
        re.compile(r"^hs\s*code$", re.I),
        re.compile(r"^hscode$", re.I),
        re.compile(r"^harmonized\s*code$", re.I),
    ],
    "storage": [re.compile(r"^storage$", re.I)],
    # Tier 3 - 상세 정보
    "eq_no": [
        re.compile(r"^eq\s*no\.?$", re.I),
        re.compile(r"^equipment\s*no$", re.I),
        re.compile(r"^equipment\s*number$", re.I),
    ],
    "site": [re.compile(r"^site$", re.I)],
    "pkg": [
        re.compile(r"^pkg$", re.I),
        re.compile(r"^package$", re.I),
        re.compile(r"^packaging$", re.I),
    ],
    "description": [
        re.compile(r"^description$", re.I),
        re.compile(r"^desc$", re.I),
        re.compile(r"^item\s*description$", re.I),
    ],
    "length_cm": [
        re.compile(r"^l\(cm\)$", re.I),
        re.compile(r"^length$", re.I),
        re.compile(r"^length\s*\(cm\)$", re.I),
    ],
    "width_cm": [
        re.compile(r"^w\(cm\)$", re.I),
        re.compile(r"^width$", re.I),
        re.compile(r"^width\s*\(cm\)$", re.I),
    ],
    "height_cm": [
        re.compile(r"^h\(cm\)$", re.I),
        re.compile(r"^height$", re.I),
        re.compile(r"^height\s*\(cm\)$", re.I),
    ],
    "cbm": [
        re.compile(r"^cbm$", re.I),
        re.compile(r"^volume$", re.I),
        re.compile(r"^cubic\s*meter$", re.I),
    ],
    "net_weight": [
        re.compile(r"^n\.w\(kgs\)$", re.I),
        re.compile(r"^net\s*weight$", re.I),
        re.compile(r"^net\s*weight\s*\(kgs\)$", re.I),
    ],
    "gross_weight": [
        re.compile(r"^g\.w\(kgs\)$", re.I),
        re.compile(r"^gross\s*weight$", re.I),
        re.compile(r"^gross\s*weight\s*\(kgs\)$", re.I),
    ],
    "stack": [re.compile(r"^stack$", re.I)],
    "currency": [re.compile(r"^currency$", re.I), re.compile(r"^curr$", re.I)],
    "price": [
        re.compile(r"^price$", re.I),
        re.compile(r"^unit\s*price$", re.I),
        re.compile(r"^unit\s*cost$", re.I),
    ],
    # 추가 필드들 (no., Shipment Invoice/DC, CODE/DC 등)
    "row_number": [
        re.compile(r"^no\.?$", re.I),
        re.compile(r"^row\s*no$", re.I),
        re.compile(r"^number$", re.I),
    ],
    "shipment_invoice": [
        re.compile(r"^shipment\s*invoice$", re.I),
        re.compile(r"^invoice\s*no$", re.I),
        re.compile(r"^invoice$", re.I),
    ],
    "code_dc": [
        re.compile(r"^code/dc$", re.I),
        re.compile(r"^code\s*/\s*dc$", re.I),
        re.compile(r"^dc\s*code$", re.I),
    ],
    "column_1": [
        re.compile(r"^열1$", re.I),
        re.compile(r"^column\s*1$", re.I),
        re.compile(r"^col1$", re.I),
    ],
}

# Columns treated as dates (force-overwrite logic applies)
DATE_CANONICAL_COLUMNS: List[str] = ["agi", "das", "mir", "shu", "eta_ata", "etd_atd"]

# For non-date columns, if True, Master non-null will overwrite Warehouse
ALWAYS_OVERWRITE_NONDATE: bool = True

# === Styles ===
HIGHLIGHT_CHANGED_DATE_HEX = "FFC000"  # Orange for date changes
HIGHLIGHT_NEW_ROW_HEX = "FFFF00"  # Yellow for new rows

ALLOW_FUZZY_COLUMN_MATCH: bool = True

# === Concurrency & batches ===
DEFAULT_MAX_WORKERS = max(2, min(32, os.cpu_count() * 2 if os.cpu_count() else 4))
DEFAULT_BATCH_SIZE = 1000  # rows per batch when computing patch plan

# === Sheet detection ===
HEADER_SCAN_MAX_ROWS = 10  # scan first N rows to locate header row
MIN_HEADER_HITS = (
    2  # minimal number of canonical headers required to accept a header row
)


@dataclass
class SyncTargets:
    master_path: str
    warehouse_path: str
    output_path: str = ""

    def __post_init__(self):
        if not self.output_path:
            root, ext = os.path.splitext(self.warehouse_path)
            self.output_path = f"{root}.synced{ext}"


@dataclass
class HeaderMap:
    """Mapping from canonical -> actual column index & header name in the sheet"""

    canonical_to_index: Dict[str, int] = field(default_factory=dict)
    index_to_name: Dict[int, str] = field(default_factory=dict)

    def require(self, key: str):
        if key not in self.canonical_to_index:
            raise KeyError(f"Required header '{key}' was not found in the sheet.")


def normalize_case_no(val) -> str:
    """Normalize CASE NO / SKU values for stable matching (strip, upper)."""
    if val is None:
        return ""
    s = str(val).strip()
    # Remove zero-width and full-width spaces
    s = s.replace("\u200b", "").replace("\u3000", "")
    return s.upper()


def is_truthy(val) -> bool:
    if val is None:
        return False
    if isinstance(val, str):
        return val.strip() != "" and val.strip().lower() not in {"nan", "none", "null"}
    return True


def canonical_name_of(header: str) -> str:
    """Return the canonical name for a given raw header if it matches any configured pattern, else ''."""
    for canon, patterns in CANONICAL_HEADER_PATTERNS.items():
        for p in patterns:
            if p.match(header.strip()):
                return canon
    return ""
