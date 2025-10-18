
"""
Master→Warehouse synchronizer (v2.9 rewrite).
- Master always takes precedence for configured columns
- Dynamic header detection (case-insensitive)
- O(n) matching via in-memory index
- Parallel plan building
- Date-change highlighting & new-row highlighting
"""
from typing import Tuple, Dict, Any
from dataclasses import dataclass
from openpyxl import load_workbook
from .sync_config import (
    SyncTargets,
    DEFAULT_MAX_WORKERS,
    DATE_CANONICAL_COLUMNS,
    HIGHLIGHT_CHANGED_DATE_HEX,
    HIGHLIGHT_NEW_ROW_HEX,
)
from .header_detector import find_header_row_and_map, pick_best_sheet
from .case_matcher import build_patch_plan, apply_patch_plan
from .excel_io import open_target_workbook, ensure_sheet_for_sync


@dataclass
class SyncResult:
    output_path: str
    stats: Dict[str, Any]


def run_sync(targets: SyncTargets, max_workers: int = DEFAULT_MAX_WORKERS) -> SyncResult:
    # 1) Open workbooks
    master_wb = open_target_workbook(targets.master_path, data_only=True)
    wh_wb = open_target_workbook(targets.warehouse_path, data_only=False)  # we will write here

    # 2) Detect sheets & headers
    master_ws, master_header_row, master_hmap = pick_best_sheet(master_wb)
    wh_ws, wh_header_row, wh_hmap = pick_best_sheet(wh_wb)

    # Ensure required headers exist
    master_hmap.require("case_no")
    wh_hmap.require("case_no")

    # 3) Build patch plan (parallelized comparison)
    plan = build_patch_plan(master_ws, master_header_row, master_hmap, wh_ws, wh_header_row, wh_hmap, DATE_CANONICAL_COLUMNS, max_workers=max_workers)

    # 4) Apply patch plan to wh_ws (in-memory)
    apply_patch_plan(
        wh_ws,
        plan,
        header_row=wh_header_row,
        highlight_date_hex=HIGHLIGHT_CHANGED_DATE_HEX,
        highlight_new_row_hex=HIGHLIGHT_NEW_ROW_HEX,
    )

    # 5) Save to output
    wh_wb.save(targets.output_path)

    # 5.1) Also dump a JSON stats sidecar for auditability
    try:
        import json, os
        sidecar = os.path.splitext(targets.output_path)[0] + '.sync_stats.json'
        with open(sidecar, 'w', encoding='utf-8') as f:
            json.dump(plan.stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # non-fatal
        pass

    # 6) Stats bundle
    return SyncResult(
        output_path=targets.output_path,
        stats=plan.stats
    )
