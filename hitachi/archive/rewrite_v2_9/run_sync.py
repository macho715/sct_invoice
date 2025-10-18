
"""
CLI entry point.
Usage:
  python -m rewrite_v2_9.run_sync --master "CASE LIST.xlsx" --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" [--out "HVDC WAREHOUSE_HITACHI(HE).synced.xlsx"]
"""
import argparse
from .sync_config import SyncTargets, DEFAULT_MAX_WORKERS
from .data_synchronizer import run_sync

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True, help="Path to CASE LIST.xlsx (Master)")
    ap.add_argument("--warehouse", required=True, help="Path to HVDC WAREHOUSE_*.xlsx (Warehouse)")
    ap.add_argument("--out", default="", help="Output path (default: <warehouse>.synced.xlsx)")
    ap.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS, help="Thread pool size")
    args = ap.parse_args()

    targets = SyncTargets(args.master, args.warehouse, args.out)
    result = run_sync(targets, max_workers=args.max_workers)
    print("=== SYNC DONE ===")
    print("Output:", result.output_path)
    print("Stats:", result.stats)

if __name__ == "__main__":
    main()
