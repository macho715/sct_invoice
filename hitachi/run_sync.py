#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hitachi CASE LIST → HVDC WAREHOUSE 동기화 실행 스크립트

이 스크립트는 hitachi 패키지를 import하여 동기화를 실행합니다.

사용법:
    python run_sync.py              # 시뮬레이션 모드
    python run_sync.py --execute    # 실제 실행
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hitachi.sync_hitachi import main

if __name__ == "__main__":
    import argparse

    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(
        description="Hitachi CASE LIST → HVDC WAREHOUSE 동기화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python run_sync.py              # 시뮬레이션 모드 (기본값)
  python run_sync.py --execute    # 실제 실행
  python run_sync.py --help       # 도움말 표시
        """,
    )
    parser.add_argument(
        "--execute", action="store_true", help="실제 실행 (기본값: dry_run 시뮬레이션)"
    )
    parser.add_argument(
        "--version", action="version", version="Hitachi 동기화 스크립트 v1.0"
    )

    args = parser.parse_args()

    # 동기화 실행
    result = main(dry_run=not args.execute)

    # 종료 코드 설정
    exit_code = 0 if result.get("success") else 1
    sys.exit(exit_code)

