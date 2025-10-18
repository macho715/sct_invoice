
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
    "case_no": [
        re.compile(r"^case\s*no\.?$", re.I),
        re.compile(r"^case[_\s-]*no$", re.I),
        re.compile(r"^sku$", re.I),
        re.compile(r"^case$", re.I),
    ],
    # Add date columns that should be force-overridden by Master
    "agi": [re.compile(r"^agi$", re.I), re.compile(r"^agi\s*date$", re.I)],
    "das": [re.compile(r"^das$", re.I), re.compile(r"^das\s*date$", re.I)],
    "mir": [re.compile(r"^mir$", re.I), re.compile(r"^mir\s*date$", re.I)],
    "shu": [re.compile(r"^shu$", re.I), re.compile(r"^shu\s*date$", re.I)],
    # Common alternates that appear in WAREHOUSE sheets
    "eta_ata": [re.compile(r"^eta/ata$", re.I)],
    "etd_atd": [re.compile(r"^etd/atd$", re.I)],
    # You can also sync free-form columns by adding keys here.
}

# Columns treated as dates (force-overwrite logic applies)
DATE_CANONICAL_COLUMNS: List[str] = ["agi", "das", "mir", "shu", "eta_ata", "etd_atd"]

# For non-date columns, if True, Master non-null will overwrite Warehouse
ALWAYS_OVERWRITE_NONDATE: bool = True

# === Styles ===
HIGHLIGHT_CHANGED_DATE_HEX = "FFC000"  # Orange for date changes
HIGHLIGHT_NEW_ROW_HEX = "FFFF00"       # Yellow for new rows

ALLOW_FUZZY_COLUMN_MATCH: bool = True

# === Concurrency & batches ===
DEFAULT_MAX_WORKERS = max(2, min(32, os.cpu_count() * 2 if os.cpu_count() else 4))
DEFAULT_BATCH_SIZE = 1000  # rows per batch when computing patch plan

# === Sheet detection ===
HEADER_SCAN_MAX_ROWS = 10  # scan first N rows to locate header row
MIN_HEADER_HITS = 2        # minimal number of canonical headers required to accept a header row


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
