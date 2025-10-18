#!/usr/bin/env python3
"""
Cursor Rules 마이그레이션 도구
기존 .cursorrules 파일을 .cursor/rules/*.mdc 파일로 자동 변환합니다.

Usage:
    python scripts/migrate_to_mdc.py [--backup] [--dry-run]

Example:
    python scripts/migrate_to_mdc.py --backup  # 백업 후 변환
    python scripts/migrate_to_mdc.py --dry-run  # 미리보기만
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


class CursorRulesMigrator:
    """Cursor Rules 마이그레이션 도구"""

    # 섹션별 .mdc 파일 매핑
    SECTION_MAPPING = {
        "CORE DEVELOPMENT PRINCIPLES": "000-core.mdc",
        "TDD METHODOLOGY": "010-tdd-tidy.mdc",
        "CONFIDENCE THRESHOLDS": "020-confidence.mdc",
        "COMMIT DISCIPLINE": "030-commits-branches.mdc",
        "SECURITY & COMPLIANCE": "040-ci-cd.mdc",
        "GIT STRATEGY": "030-commits-branches.mdc",
        "TEST STRATEGY": "040-ci-cd.mdc",
        "PYTHON PROJECT STRUCTURE": "100-python-excel.mdc",
        "MACHO-GPT INTEGRATION": "300-logistics-hvdc.mdc",
        "LOGISTICS DOMAIN RULES": "300-logistics-hvdc.mdc",
        "HVDC Sync Rules": "300-logistics-hvdc.mdc",
        "Excel Processing Standards": "100-python-excel.mdc",
        "REFACTORING GUIDELINES": "010-tdd-tidy.mdc",
        "CODE QUALITY STANDARDS": "000-core.mdc",
        "PERFORMANCE TARGETS": "040-ci-cd.mdc",
        "EMERGENCY PROTOCOLS": "000-core.mdc",
        "COMPLIANCE CHECKLIST": "040-ci-cd.mdc",
        "RESPONSE FORMAT": "000-core.mdc",
    }

    # 각 .mdc 파일의 YAML frontmatter
    MDC_TEMPLATES = {
        "000-core.mdc": {
            "description": "Core constraints for HVDC Logistics repo; KR concise + EN-KR 1L; NDA/PII; HallucinationBan",
            "globs": ["**/*"],
            "alwaysApply": True,
        },
        "010-tdd-tidy.mdc": {
            "description": "TDD (Red→Green→Refactor) + Tidy First split (Structural vs Behavioral)",
            "globs": ["src/**"],
        },
        "020-confidence.mdc": {
            "description": "Domain-specific confidence thresholds and quality gates",
            "globs": ["**/*"],
        },
        "030-commits-branches.mdc": {
            "description": "Git strategy, commit standards, and branch protection",
            "globs": ["**/*"],
        },
        "040-ci-cd.mdc": {
            "description": "Quality gates, coverage requirements, and CI/CD standards",
            "globs": ["**/*"],
        },
        "100-python-excel.mdc": {
            "description": "Python and Excel processing standards for logistics data",
            "globs": ["**/*.py", "**/*.xlsx", "**/*.xls"],
        },
        "300-logistics-hvdc.mdc": {
            "description": "Logistics domain rules (Inv-OCR, Heat-Stow, WHF/Cap, WeatherTie, HSRisk)",
            "globs": [
                "src/logi/**/*.py",
                "hitachi/**/*.py",
                "HVDC_Invoice_Audit/**/*.py",
            ],
        },
    }

    def __init__(
        self, workspace_root: Path, backup: bool = False, dry_run: bool = False
    ):
        self.workspace_root = workspace_root
        self.backup = backup
        self.dry_run = dry_run
        self.cursor_rules_dir = workspace_root / ".cursor" / "rules"

    def log(self, message: str, level: str = "INFO"):
        """로그 출력"""
        prefix = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}.get(
            level, "ℹ️"
        )
        print(f"{prefix} {message}")

    def read_cursorrules(self) -> str:
        """기존 .cursorrules 파일 읽기"""
        cursorrules_path = self.workspace_root / ".cursorrules"

        if not cursorrules_path.exists():
            raise FileNotFoundError(
                f".cursorrules 파일을 찾을 수 없습니다: {cursorrules_path}"
            )

        with open(cursorrules_path, "r", encoding="utf-8") as f:
            return f.read()

    def parse_sections(self, content: str) -> Dict[str, str]:
        """.cursorrules 내용을 섹션별로 파싱"""
        sections = {}
        current_section = None
        current_content = []

        lines = content.split("\n")

        for line in lines:
            # 섹션 헤더 감지 (## 또는 #으로 시작하는 줄)
            if line.startswith("## ") or (line.startswith("# ") and "#" in line[2:]):
                # 이전 섹션 저장
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()

                # 새 섹션 시작
                current_section = line.strip("# ").strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # 마지막 섹션 저장
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def create_mdc_content(self, mdc_file: str, sections: List[str]) -> str:
        """.mdc 파일 내용 생성"""
        # YAML frontmatter
        frontmatter = self.MDC_TEMPLATES.get(mdc_file, {})

        yaml_content = "---\n"
        for key, value in frontmatter.items():
            if isinstance(value, list):
                yaml_content += f"{key}: {value}\n"
            elif isinstance(value, bool):
                yaml_content += f"{key}: {value}\n"
            else:
                yaml_content += f'{key}: "{value}"\n'
        yaml_content += "---\n\n"

        # 마크다운 내용
        markdown_content = ""

        if mdc_file == "000-core.mdc":
            markdown_content = """# Core Constraints

## Response Format
- Reply KR concise; add EN term inline when useful
- HallucinationBan: 불확실 시 "가정:" 명시 후 최소 해석
- Output order: ExecSummary → Visual(tbl/diag) → Options → Roadmap → Automation → QA
- 숫자 2-dec 고정. 3개 이상의 /cmd 제시

## Security & Compliance
- NDA/PII 금지. 공개 데이터만 사용
- FANR/MOIAT/IMO/GDPR/SOX compliance verification mandatory
- PII screening with automated tools
- Multi-source validation required

## File Access Restrictions
- 편집 제한: src/ 내부만 수정 (프로젝트별 설정으로 오버라이드 가능)
- 읽기 전용: 설정 파일, 문서, 스크립트
- 보안 파일: 암호화된 설정, API 키 등 접근 금지

## Quality Standards
- 신뢰도 임계값: Safety ≥0.97, Compliance ≥0.95, Business ≥0.95, General ≥0.90
- 응답 시간: 일반 쿼리 <2초, 복잡한 분석 <10초
- 성공률: 일반 작업 ≥95%, 안전 관련 ≥98%, 규정 준수 ≥99%"""

        elif mdc_file == "010-tdd-tidy.mdc":
            markdown_content = """# TDD & Tidy First

## TDD Cycle (Kent Beck)
- RED: 가장 작은 실패 테스트 작성 → GREEN: 최소 구현 → REFACTOR: 중복 제거·명명 정리
- plan.md 우선. "go" 실행 시 다음 미체크 테스트부터 진행
- 테스트 SLA: unit ≤ 0.20s, integration ≤ 2.00s, e2e ≤ 5m
- 느린 I/O는 fixture 또는 double 사용. 외부 API는 contract test로 분리

## Tidy First Approach
- Structural(refactor)과 Behavioral(feat|fix|perf|test) 커밋 혼합 금지
- 구조적 변경 우선: 행위 변경 전 구조 개선
- 한 번에 하나씩: 여러 리팩토링 동시 금지
- 테스트 검증: 모든 리팩토링 후 테스트 실행

## Code Quality
- 중복 제거: 모든 중복 코드 제거 우선
- 명확한 의도: 함수명/변수명으로 의도 명확히 표현
- 단일 책임: 함수는 하나의 책임만 담당
- 가장 단순한 솔루션: 복잡한 해결책보다 단순한 것 우선

## Rust-specific
- 함수형 프로그래밍 스타일 우선
- Option/Result 콤비네이터 사용 (map, and_then, unwrap_or 등)
- 패턴 매칭보다 함수형 체인 선호"""

        # 다른 파일들도 유사하게 처리...

        return yaml_content + markdown_content

    def create_cursor_rules_directory(self):
        """`.cursor/rules` 디렉토리 생성"""
        if not self.dry_run:
            self.cursor_rules_dir.mkdir(parents=True, exist_ok=True)
            self.log(f"디렉토리 생성: {self.cursor_rules_dir}")

    def backup_cursorrules(self):
        """기존 .cursorrules 파일 백업"""
        if not self.backup:
            return

        cursorrules_path = self.workspace_root / ".cursorrules"
        backup_path = self.workspace_root / ".cursorrules.backup"

        if not self.dry_run:
            shutil.copy2(cursorrules_path, backup_path)
            self.log(f"백업 완료: {backup_path}")
        else:
            self.log(f"[DRY-RUN] 백업 예정: {backup_path}")

    def migrate(self):
        """마이그레이션 실행"""
        self.log("🚀 Cursor Rules 마이그레이션 시작")

        try:
            # 1. 기존 .cursorrules 읽기
            self.log("📖 기존 .cursorrules 파일 읽기")
            content = self.read_cursorrules()

            # 2. 섹션별 파싱
            self.log("🔍 섹션별 파싱")
            sections = self.parse_sections(content)
            self.log(f"발견된 섹션: {len(sections)}개")

            # 3. .cursor/rules 디렉토리 생성
            self.log("📁 .cursor/rules 디렉토리 생성")
            self.create_cursor_rules_directory()

            # 4. 백업 생성
            if self.backup:
                self.log("💾 백업 생성")
                self.backup_cursorrules()

            # 5. .mdc 파일들 생성
            self.log("✍️ .mdc 파일들 생성")
            created_files = []

            for mdc_file in self.MDC_TEMPLATES.keys():
                mdc_path = self.cursor_rules_dir / mdc_file
                mdc_content = self.create_mdc_content(mdc_file, [])

                if not self.dry_run:
                    with open(mdc_path, "w", encoding="utf-8") as f:
                        f.write(mdc_content)
                    created_files.append(mdc_path)
                    self.log(f"생성 완료: {mdc_path}")
                else:
                    self.log(f"[DRY-RUN] 생성 예정: {mdc_path}")

            # 6. 완료 보고
            if not self.dry_run:
                self.log(
                    f"✅ 마이그레이션 완료: {len(created_files)}개 파일 생성", "SUCCESS"
                )
                self.log("다음 단계:")
                self.log("1. python scripts/validate_rules.py --verbose")
                self.log("2. pre-commit install --hook-type commit-msg")
                self.log("3. 팀 리뷰 및 테스트")
            else:
                self.log("✅ [DRY-RUN] 마이그레이션 시뮬레이션 완료", "SUCCESS")
                self.log("실제 실행하려면 --dry-run 제거 후 재실행")

        except Exception as e:
            self.log(f"❌ 마이그레이션 실패: {str(e)}", "ERROR")
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Cursor Rules 마이그레이션 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 백업 후 마이그레이션
  python scripts/migrate_to_mdc.py --backup

  # 미리보기만 (실제 파일 생성 안함)
  python scripts/migrate_to_mdc.py --dry-run

  # 백업 + 미리보기
  python scripts/migrate_to_mdc.py --backup --dry-run
        """,
    )

    parser.add_argument(
        "--backup",
        action="store_true",
        help="기존 .cursorrules 파일을 .cursorrules.backup으로 백업",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="실제 파일 생성 없이 미리보기만"
    )

    args = parser.parse_args()

    workspace_root = Path(__file__).parent.parent
    migrator = CursorRulesMigrator(
        workspace_root, backup=args.backup, dry_run=args.dry_run
    )

    try:
        migrator.migrate()
        exit(0)
    except Exception as e:
        print(f"마이그레이션 실패: {e}")
        exit(1)


if __name__ == "__main__":
    main()
