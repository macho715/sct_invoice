from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

@dataclass
class CaseChange:
    case_no: str
    column: str
    old: Any
    new: Any
    change_type: str = "cell_update"
    priority: Optional[str] = None

class UpdateTracker:
    def __init__(self, out_dir: Optional[str] = None) -> None:
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if out_dir is None:
            # 스크립트 위치 기준으로 hitachi/out/ 경로 설정
            script_dir = Path(__file__).parent.parent  # hitachi/ 폴더
            out_dir = script_dir / "out"
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.before: Dict[str, pd.DataFrame] = {}
        self.after: Dict[str, pd.DataFrame] = {}
        self.total_cases: int = 0
        self.warehouse_columns: List[str] = []
        self.changes: List[CaseChange] = []
        self.new_cases: Dict[str, Dict[str, Any]] = {}
        self._started: bool = False

    def capture_before_state(self, df: pd.DataFrame, sheet_name: str) -> None:
        self.before[sheet_name] = df.copy()

    def capture_after_state(self, df: pd.DataFrame, sheet_name: str) -> None:
        self.after[sheet_name] = df.copy()

    def start_update_tracking(self, total_cases: int, warehouse_columns: List[str]) -> None:
        self.total_cases = int(total_cases or 0)
        self.warehouse_columns = list(warehouse_columns or [])
        self._started = True

    def log_case_update(self, case_no: str, changes: List[Dict[str, Any]],
                        force_change_type: str = None, force_priority: str = None) -> None:
        for ch in changes or []:
            ctype = force_change_type or ch.get("change_type") or "cell_update"
            prio = force_priority or ch.get("priority")
            self.changes.append(
                CaseChange(case_no=case_no,
                           column=ch.get("column"),
                           old=ch.get("old"),
                           new=ch.get("new"),
                           change_type=ctype,
                           priority=prio)
            )

    def log_new_case(self, case_no: str, row_data: Dict[str, Any]) -> None:
        self.new_cases[str(case_no)] = dict(row_data or {})

    def end_update_tracking(self) -> Dict[str, Any]:
        return self.generate_change_comparison_report()

    def create_change_heatmap(self) -> str:
        if not self.changes:
            fig, ax = plt.subplots()
            ax.set_title("No changes")
            png = self.out_dir / f"change_heatmap_{self.run_id}.png"
            fig.savefig(png, bbox_inches='tight')
            plt.close(fig)
            return str(png)

        df = pd.DataFrame([asdict(c) for c in self.changes])
        counts = df.groupby('column').size().sort_values(ascending=False)

        fig, ax = plt.subplots()
        counts.plot(kind='bar', ax=ax)
        ax.set_title('Changes per Column')
        ax.set_xlabel('Column')
        ax.set_ylabel('Count')
        png = self.out_dir / f"change_heatmap_{self.run_id}.png"
        fig.tight_layout()
        fig.savefig(png, bbox_inches='tight')
        plt.close(fig)
        return str(png)

    def generate_detailed_report(self) -> str:
        rows = [asdict(c) for c in self.changes]
        csv_path = self.out_dir / f"update_details_{self.run_id}.csv"
        import pandas as pd
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        return str(csv_path)

    def generate_change_comparison_report(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "run_id": self.run_id,
            "total_cases": self.total_cases,
            "new_cases": list(self.new_cases.keys()),
            "counts": {"total_changes": len(self.changes),
                       "by_type": {},
                       "by_priority": {}},
        }
        if self.changes:
            import pandas as pd
            df = pd.DataFrame([asdict(c) for c in self.changes])
            by_type = df.groupby('change_type').size().to_dict()
            by_prio = df.groupby('priority').size().to_dict()
            summary["counts"]["by_type"] = {str(k): int(v) for k, v in by_type.items()}
            summary["counts"]["by_priority"] = {str(k): int(v) for k, v in by_prio.items()}
        return summary
