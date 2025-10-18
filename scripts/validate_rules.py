#!/usr/bin/env python3
"""
Cursor Rules 검증 스크립트
.cursorrules 및 .cursorrules.project 파일의 유효성을 검증합니다.

Usage:
    python scripts/validate_rules.py [--fix] [--verbose]

Example:
    python scripts/validate_rules.py --verbose
    python scripts/validate_rules.py --fix  # 자동 수정 시도
"""

import os
import re
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """검증 결과"""

    file_path: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


class RulesValidator:
    """Cursor Rules 검증기"""

    # 필수 .mdc 파일들
    REQUIRED_MDC_FILES = [
        "000-core.mdc",
        "010-tdd-tidy.mdc",
        "020-confidence.mdc",
        "030-commits-branches.mdc",
        "040-ci-cd.mdc",
        "100-python-excel.mdc",
        "300-logistics-hvdc.mdc",
    ]

    # 필수 섹션 (루트 .cursorrules - 참조용)
    REQUIRED_SECTIONS_ROOT = [
        "CORE DEVELOPMENT PRINCIPLES",
        "COMMIT DISCIPLINE",
        "TEST STRATEGY",
        "CONFIDENCE THRESHOLDS",
        "SECURITY & COMPLIANCE",
        "GIT STRATEGY",
    ]

    # 필수 필드 (프로젝트별)
    REQUIRED_FIELDS_PROJECT = [
        "project_name",
        "version",
        "domain",
    ]

    # 커밋 타입 검증
    VALID_COMMIT_TYPES = [
        "STRUCT",
        "FEAT",
        "FIX",
        "PERF",
        "MODE",
        "CMD",
        "TEST",
        "DOCS",
    ]

    def __init__(self, fix_mode: bool = False, verbose: bool = False):
        self.fix_mode = fix_mode
        self.verbose = verbose
        self.workspace_root = Path(__file__).parent.parent

    def log(self, message: str, level: str = "INFO"):
        """로그 출력"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}.get(
                level, "ℹ️"
            )
            print(f"{prefix} {message}")

    def find_rules_files(self) -> List[Path]:
        """Rules 파일 찾기"""
        rules_files = []

        # .cursor/rules/*.mdc 파일들
        cursor_rules_dir = self.workspace_root / ".cursor" / "rules"
        if cursor_rules_dir.exists():
            for mdc_file in cursor_rules_dir.glob("*.mdc"):
                rules_files.append(mdc_file)

        # 루트 .cursorrules (참조용)
        root_rules = self.workspace_root / ".cursorrules"
        if root_rules.exists():
            rules_files.append(root_rules)

        # 프로젝트별 .cursorrules.project
        for project_rules in self.workspace_root.rglob(".cursorrules.project"):
            rules_files.append(project_rules)

        return rules_files

    def validate_mdc_file(self, file_path: Path) -> ValidationResult:
        """`.cursor/rules/*.mdc` 파일 검증"""
        errors = []
        warnings = []
        info = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # YAML frontmatter 검증
            if not content.startswith("---"):
                errors.append("YAML frontmatter 누락 (---로 시작해야 함)")
            else:
                # frontmatter 추출
                frontmatter_end = content.find("---", 3)
                if frontmatter_end == -1:
                    errors.append("YAML frontmatter 불완전 (---로 끝나야 함)")
                else:
                    frontmatter = content[3:frontmatter_end].strip()
                    try:
                        yaml_data = yaml.safe_load(frontmatter)

                        # 필수 필드 검증
                        required_fields = ["description", "globs"]
                        for field in required_fields:
                            if field not in yaml_data:
                                errors.append(f"필수 필드 누락: {field}")

                        # globs 패턴 검증
                        if "globs" in yaml_data:
                            globs = yaml_data["globs"]
                            if not isinstance(globs, list):
                                errors.append("globs는 리스트여야 함")
                            else:
                                for glob_pattern in globs:
                                    if not isinstance(glob_pattern, str):
                                        errors.append(
                                            f"glob 패턴이 문자열이 아님: {glob_pattern}"
                                        )

                        # alwaysApply 검증
                        if "alwaysApply" in yaml_data:
                            if not isinstance(yaml_data["alwaysApply"], bool):
                                warnings.append("alwaysApply는 boolean이어야 함")

                    except yaml.YAMLError as e:
                        errors.append(f"YAML 문법 오류: {str(e)}")

            # 파일명 검증
            expected_name = file_path.name
            if expected_name not in self.REQUIRED_MDC_FILES:
                warnings.append(f"예상되지 않은 .mdc 파일: {expected_name}")

            # 내용 검증 (기본적인 키워드)
            if "description" in content and "globs" in content:
                info.append("기본 구조 정상")

            info.append(f"파일 크기: {len(content)} bytes")
            info.append(f"라인 수: {content.count(chr(10)) + 1}")

        except Exception as e:
            errors.append(f"파일 읽기 실패: {str(e)}")

        is_valid = len(errors) == 0
        return ValidationResult(str(file_path), is_valid, errors, warnings, info)

    def validate_root_rules(self, file_path: Path) -> ValidationResult:
        """루트 .cursorrules 검증"""
        errors = []
        warnings = []
        info = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 필수 섹션 검증
            for section in self.REQUIRED_SECTIONS_ROOT:
                if section not in content:
                    errors.append(f"필수 섹션 누락: {section}")

            # 커밋 메시지 형식 검증
            commit_pattern = r"\[TYPE\] scope: description"
            if commit_pattern not in content:
                warnings.append("커밋 메시지 형식 예제 누락")

            # TYPE 정의 검증
            for commit_type in self.VALID_COMMIT_TYPES:
                if (
                    f"`{commit_type}`" not in content
                    and f"{commit_type}:" not in content
                ):
                    warnings.append(f"커밋 타입 정의 누락: {commit_type}")

            # 테스트 SLA 검증
            if "test_sla:" in content:
                if "unit:" not in content:
                    errors.append("test_sla에 unit 필드 누락")
                if "integration:" not in content:
                    errors.append("test_sla에 integration 필드 누락")

            # Confidence threshold 검증
            if "confidence_threshold:" in content:
                thresholds = re.findall(r"(\w+_critical):\s*(0\.\d+)", content)
                for name, value in thresholds:
                    val = float(value)
                    if val < 0.80 or val > 1.0:
                        warnings.append(
                            f"신뢰도 임계값 범위 이상: {name}={val} (권장: 0.80-1.0)"
                        )

            # Git 전략 검증
            if "git_strategy:" in content:
                if "protected_branches:" not in content:
                    warnings.append("protected_branches 미정의")
                if "pr_requirements:" not in content:
                    warnings.append("pr_requirements 미정의")

            # 보안 도구 검증
            if "security_tools:" in content:
                security_tools = ["bandit", "safety", "semgrep"]
                for tool in security_tools:
                    if tool not in content:
                        warnings.append(f"권장 보안 도구 누락: {tool}")

            info.append(f"파일 크기: {len(content)} bytes")
            info.append(f"라인 수: {content.count(chr(10)) + 1}")

        except Exception as e:
            errors.append(f"파일 읽기 실패: {str(e)}")

        is_valid = len(errors) == 0
        return ValidationResult(str(file_path), is_valid, errors, warnings, info)

    def validate_project_rules(self, file_path: Path) -> ValidationResult:
        """프로젝트별 .cursorrules.project 검증"""
        errors = []
        warnings = []
        info = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # extends 검증
            if "extends:" not in content and "Extends:" not in content:
                warnings.append("extends 필드 권장 (부모 규칙 상속)")

            # 필수 필드 검증
            for field in self.REQUIRED_FIELDS_PROJECT:
                if f"{field}:" not in content:
                    errors.append(f"필수 필드 누락: {field}")

            # 프로젝트별 특화 규칙 검증
            project_dir = file_path.parent.name

            if project_dir == "hitachi":
                # Hitachi 특화 검증
                required = [
                    "master_precedence",
                    "header_normalization",
                    "performance_target",
                ]
                for req in required:
                    if req not in content:
                        errors.append(f"Hitachi 필수 설정 누락: {req}")

            elif "HVDC_Invoice_Audit" in str(file_path):
                # MACHO 특화 검증
                required = ["containment_modes", "auto_triggers", "confidence_min"]
                for req in required:
                    if req not in content:
                        errors.append(f"MACHO 필수 설정 누락: {req}")

            elif project_dir == "ML":
                # ML 특화 검증
                required = ["model_validation", "training_data"]
                for req in required:
                    if req not in content:
                        errors.append(f"ML 필수 설정 누락: {req}")

            # YAML 문법 검증 (YAML 블록이 있는 경우)
            yaml_blocks = re.findall(r"```yaml\n(.*?)\n```", content, re.DOTALL)
            for i, block in enumerate(yaml_blocks):
                try:
                    yaml.safe_load(block)
                except yaml.YAMLError as e:
                    errors.append(f"YAML 문법 오류 (블록 {i+1}): {str(e)}")

            info.append(f"프로젝트: {project_dir}")
            info.append(f"파일 크기: {len(content)} bytes")

        except Exception as e:
            errors.append(f"파일 읽기 실패: {str(e)}")

        is_valid = len(errors) == 0
        return ValidationResult(str(file_path), is_valid, errors, warnings, info)

    def validate_file(self, file_path: Path) -> ValidationResult:
        """파일 검증"""
        if file_path.name.endswith(".mdc"):
            return self.validate_mdc_file(file_path)
        elif file_path.name == ".cursorrules":
            return self.validate_root_rules(file_path)
        else:
            return self.validate_project_rules(file_path)

    def detect_conflicts(self, results: List[ValidationResult]) -> List[str]:
        """규칙 충돌 감지"""
        conflicts = []

        # 여기서는 간단한 예시만 구현
        # 실제로는 더 복잡한 충돌 감지 로직 필요

        # 예: 동일한 설정이 다른 값으로 정의된 경우
        # 이는 파일 내용을 파싱하여 비교해야 함

        return conflicts

    def print_result(self, result: ValidationResult):
        """결과 출력"""
        print(f"\n{'='*80}")
        print(f"📄 파일: {result.file_path}")
        print(f"{'='*80}")

        if result.is_valid:
            print("✅ 검증 통과")
        else:
            print("❌ 검증 실패")

        if result.errors:
            print(f"\n❌ 오류 ({len(result.errors)}개):")
            for error in result.errors:
                print(f"  - {error}")

        if result.warnings:
            print(f"\n⚠️ 경고 ({len(result.warnings)}개):")
            for warning in result.warnings:
                print(f"  - {warning}")

        if self.verbose and result.info:
            print(f"\nℹ️ 정보:")
            for info in result.info:
                print(f"  - {info}")

    def validate_all(self) -> Tuple[int, int, int]:
        """모든 규칙 파일 검증"""
        self.log("🔍 Cursor Rules 파일 검색 중...")
        rules_files = self.find_rules_files()

        if not rules_files:
            self.log("⚠️ Rules 파일을 찾을 수 없습니다.", "WARNING")
            return (0, 0, 0)

        self.log(f"📋 총 {len(rules_files)}개 파일 발견", "INFO")

        results = []
        for file_path in rules_files:
            self.log(f"검증 중: {file_path.name}", "INFO")
            result = self.validate_file(file_path)
            results.append(result)
            self.print_result(result)

        # 충돌 감지
        conflicts = self.detect_conflicts(results)
        if conflicts:
            print(f"\n⚠️ 규칙 충돌 감지:")
            for conflict in conflicts:
                print(f"  - {conflict}")

        # 통계
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        print(f"\n{'='*80}")
        print(f"📊 검증 결과 요약")
        print(f"{'='*80}")
        print(f"총 파일: {total}")
        print(f"✅ 통과: {valid}")
        print(f"❌ 실패: {invalid}")

        if invalid == 0:
            print("\n🎉 모든 규칙 파일이 유효합니다!")
        else:
            print(f"\n⚠️ {invalid}개 파일에 문제가 있습니다. 위 내용을 확인하세요.")

        return (total, valid, invalid)


def main():
    parser = argparse.ArgumentParser(
        description="Cursor Rules 파일 검증",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 기본 검증
  python scripts/validate_rules.py

  # 상세 정보 출력
  python scripts/validate_rules.py --verbose

  # 자동 수정 시도 (향후 구현)
  python scripts/validate_rules.py --fix
        """,
    )

    parser.add_argument(
        "--fix", action="store_true", help="자동 수정 시도 (일부 문제만 해당)"
    )

    parser.add_argument("--verbose", action="store_true", help="상세 정보 출력")

    args = parser.parse_args()

    validator = RulesValidator(fix_mode=args.fix, verbose=args.verbose)
    total, valid, invalid = validator.validate_all()

    # Exit code: 실패한 파일이 있으면 1
    exit(0 if invalid == 0 else 1)


if __name__ == "__main__":
    main()
