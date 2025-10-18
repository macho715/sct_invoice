from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

DATE_KEYS = ('date','eta','etd','ata','atd','mosb','mir','shu','das','agi','shifting')

@dataclass
class ChangeRecord:
    case_no: str
    column_name: str
    old_value: Any
    new_value: Any
    change_type: str = "cell_update"
    priority: Optional[str] = None
    row_index: Optional[int] = None

class ChangeTracker:
    def __init__(self) -> None:
        self.changes: List[ChangeRecord] = []
        self.date_changes: Dict[str, List[Dict[str, Any]]] = {}
        self._new_cases: Set[str] = set()

    def get_new_cases(self) -> Set[str]:
        return set(self._new_cases)

    def generate_summary(self) -> Dict[str, Any]:
        total = len(self.changes)
        by_type: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        for ch in self.changes:
            by_type[ch.change_type] = by_type.get(ch.change_type, 0) + 1
            key = ch.priority or "none"
            by_priority[key] = by_priority.get(key, 0) + 1
        return {
            "total": total,
            "by_type": by_type,
            "by_priority": by_priority,
            "new_cases": sorted(list(self._new_cases)),
        }

    def add_change(self, case_no: str, column_name: str, old_value: Any, new_value: Any,
                   change_type: str = "cell_update", priority: Optional[str] = None,
                   row_index: Optional[int] = None) -> None:
        rec = ChangeRecord(case_no=case_no, column_name=column_name,
                           old_value=old_value, new_value=new_value,
                           change_type=change_type, priority=priority,
                           row_index=row_index)
        self.changes.append(rec)
        if any(k in str(column_name).lower() for k in DATE_KEYS) or change_type == "date_update":
            self.date_changes.setdefault(case_no, []).append({
                "column": column_name, "old": old_value, "new": new_value,
                "priority": priority, "row_index": row_index
            })

    def log_new_case(self, case_no: str) -> None:
        self._new_cases.add(str(case_no))

    def get_changes_by_case(self, case_no: str) -> Dict[str, Tuple[Any, Any]]:
        out: Dict[str, Tuple[Any, Any]] = {}
        for ch in self.changes:
            if str(ch.case_no) == str(case_no):
                out[str(ch.column_name)] = (ch.old_value, ch.new_value)
        return out

    def clear(self) -> None:
        self.changes.clear()
        self.date_changes.clear()
        self._new_cases.clear()
