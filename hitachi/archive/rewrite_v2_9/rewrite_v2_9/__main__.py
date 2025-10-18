"""
Main entry point for the rewrite_v2_9 package.

Usage:
    python -m rewrite_v2_9.rewrite_v2_9 --master "CASE LIST.xlsx" --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx"
"""

from .run_sync import main

if __name__ == "__main__":
    main()
