from __future__ import annotations
import re
from typing import Any, Dict

class HVDCValidator:
    @staticmethod
    def validate_hvdc_code(code: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "valid": False,
            "formatted_code": None,
            "manufacturer": None,
            "sequence": None,
            "original_code": code,
            "was_normalized": False,
            "error": None,
        }
        if code is None:
            result["error"] = "empty"
            return result

        raw = str(code).strip()
        compact = re.sub(r"[\s_]+", "-", raw).upper()
        compact = re.sub(r"-+", "-", compact).strip("-")

        strict = re.match(r"^HVDC-ADOPT-(HE|SIM)-(\d{1,4})$", compact)
        tolerant = re.match(r"^HVDC\s*-?\s*ADOPT\s*-?\s*(HE|SIM)\s*-?\s*(\d{1,4})$", raw, flags=re.IGNORECASE)
        m = strict or tolerant
        if not m:
            result["error"] = f"invalid format: {raw}"
            return result

        manufacturer = m.group(1).upper()
        seq_str = m.group(2)
        try:
            seq = int(seq_str)
        except Exception:
            result["error"] = f"sequence not numeric: {seq_str}"
            return result

        if not (1 <= seq <= 9999):
            result["error"] = f"sequence out of range: {seq}"
            return result

        formatted = f"HVDC-ADOPT-{manufacturer}-{seq:04d}"
        result.update(
            valid=True,
            formatted_code=formatted,
            manufacturer=manufacturer,
            sequence=seq,
            was_normalized=(formatted != raw),
            error=None,
        )
        return result
