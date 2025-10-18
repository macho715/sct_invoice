#!/usr/bin/env python3
"""
CHANGELOG 자동 생성 스크립트
Git 커밋 히스토리를 파싱하여 CHANGELOG.md를 자동 생성/업데이트합니다.

Usage:
    python scripts/generate_changelog.py [--since VERSION] [--output PATH]

Example:
    python scripts/generate_changelog.py --since v1.0.0 --output CHANGELOG.md
"""

import subprocess
import re
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple
import argparse


class ChangelogGenerator:
    """Git 커밋 히스토리 기반 CHANGELOG 생성기"""

    # 커밋 타입별 한글 레이블
    TYPE_LABELS = {
        "STRUCT": "🏗️ 구조 개선",
        "FEAT": "✨ 새 기능",
        "FIX": "🐛 버그 수정",
        "PERF": "⚡ 성능 개선",
        "MODE": "🎯 모드 변경",
        "CMD": "🔧 명령어",
        "TEST": "🧪 테스트",
        "DOCS": "📚 문서",
        "STYLE": "💄 스타일",
        "REFACTOR": "♻️ 리팩토링",
        "CHORE": "🔨 기타",
    }

    def __init__(self, since_tag: str = None, output_path: str = "CHANGELOG.md"):
        self.since_tag = since_tag
        self.output_path = output_path

    def get_git_log(self) -> List[str]:
        """Git 로그 가져오기"""
        cmd = ["git", "log", "--pretty=format:%H|%ai|%an|%s"]

        if self.since_tag:
            cmd.append(f"{self.since_tag}..HEAD")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip().split("\n")
        except subprocess.CalledProcessError as e:
            print(f"Git 로그 가져오기 실패: {e}")
            return []

    def parse_commit(self, commit_line: str) -> Tuple[str, str, str, str, str, str]:
        """커밋 라인 파싱"""
        parts = commit_line.split("|")
        if len(parts) != 4:
            return None

        commit_hash, date_str, author, message = parts

        # 커밋 메시지 파싱: [TYPE] scope: description
        pattern = r"^\[([A-Z]+)\]\s*([^:]*?):\s*(.+)$"
        match = re.match(pattern, message.strip())

        if match:
            commit_type = match.group(1)
            scope = match.group(2).strip()
            description = match.group(3).strip()
        else:
            # 표준 형식이 아닌 경우
            commit_type = "CHORE"
            scope = ""
            description = message.strip()

        # 날짜 파싱 (YYYY-MM-DD만)
        date = date_str.split()[0]

        return (commit_hash[:7], date, author, commit_type, scope, description)

    def group_commits(self, commits: List[Tuple]) -> Dict[str, List[Dict]]:
        """커밋을 타입별로 그룹핑"""
        grouped = defaultdict(list)

        for commit in commits:
            if not commit:
                continue

            hash_short, date, author, commit_type, scope, description = commit

            grouped[commit_type].append(
                {
                    "hash": hash_short,
                    "date": date,
                    "author": author,
                    "scope": scope,
                    "description": description,
                }
            )

        return grouped

    def generate_changelog_content(self, grouped_commits: Dict) -> str:
        """CHANGELOG 콘텐츠 생성"""
        lines = []

        # 헤더
        lines.append("# CHANGELOG\n")
        lines.append(
            "이 프로젝트의 모든 주목할 만한 변경 사항은 이 파일에 문서화됩니다.\n"
        )
        lines.append(
            f'마지막 업데이트: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        )
        lines.append("---\n")

        # 버전 섹션 (현재는 Unreleased)
        if self.since_tag:
            version_title = f"## [Unreleased] - since {self.since_tag}"
        else:
            version_title = "## [Unreleased]"

        lines.append(f"{version_title}\n")

        # 타입별로 커밋 정리
        type_order = [
            "FEAT",
            "PERF",
            "FIX",
            "STRUCT",
            "MODE",
            "CMD",
            "TEST",
            "DOCS",
            "STYLE",
            "REFACTOR",
            "CHORE",
        ]

        for commit_type in type_order:
            if commit_type not in grouped_commits:
                continue

            commits = grouped_commits[commit_type]
            if not commits:
                continue

            label = self.TYPE_LABELS.get(commit_type, commit_type)
            lines.append(f"\n### {label}\n")

            for commit in commits:
                scope_str = f"**{commit['scope']}**: " if commit["scope"] else ""
                line = f"- {scope_str}{commit['description']} ({commit['hash']})"
                lines.append(line)

        lines.append("\n---\n")

        return "\n".join(lines)

    def update_changelog_file(self, new_content: str):
        """CHANGELOG 파일 업데이트 (기존 내용 유지)"""
        try:
            # 기존 CHANGELOG 읽기
            try:
                with open(self.output_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
            except FileNotFoundError:
                existing_content = ""

            # Unreleased 섹션만 교체
            if existing_content and "## [Unreleased]" in existing_content:
                # 기존 Unreleased 섹션 제거
                parts = existing_content.split("---")
                if len(parts) > 2:
                    # 헤더 + 새 Unreleased + 나머지 버전들
                    header = parts[0]
                    rest_versions = "---".join(parts[2:])

                    # 새 콘텐츠에서 Unreleased 섹션만 추출
                    new_parts = new_content.split("---")
                    new_unreleased = "---".join(new_parts[:2]) + "---"

                    final_content = f"{new_unreleased}\n{rest_versions}"
                else:
                    final_content = new_content
            else:
                final_content = new_content

            # 파일 쓰기
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(final_content)

            print(f"✅ CHANGELOG 업데이트 완료: {self.output_path}")

        except Exception as e:
            print(f"❌ CHANGELOG 파일 업데이트 실패: {e}")

    def generate(self):
        """CHANGELOG 생성 메인 로직"""
        print("📋 Git 커밋 히스토리 수집 중...")
        log_lines = self.get_git_log()

        if not log_lines:
            print("⚠️ 커밋 히스토리가 없습니다.")
            return

        print(f"📊 총 {len(log_lines)}개 커밋 발견")

        print("🔍 커밋 파싱 중...")
        commits = [self.parse_commit(line) for line in log_lines if line]
        commits = [c for c in commits if c]  # None 제거

        print("📦 타입별 그룹핑 중...")
        grouped = self.group_commits(commits)

        # 통계 출력
        print("\n📈 커밋 통계:")
        for commit_type, commits_list in sorted(grouped.items()):
            label = self.TYPE_LABELS.get(commit_type, commit_type)
            print(f"  {label}: {len(commits_list)}개")

        print("\n✍️ CHANGELOG 생성 중...")
        content = self.generate_changelog_content(grouped)

        print("💾 CHANGELOG 파일 업데이트 중...")
        self.update_changelog_file(content)


def main():
    parser = argparse.ArgumentParser(
        description="Git 커밋 히스토리로부터 CHANGELOG.md 자동 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 전체 히스토리로 CHANGELOG 생성
  python scripts/generate_changelog.py

  # 특정 태그 이후 변경사항만
  python scripts/generate_changelog.py --since v1.0.0

  # 출력 파일 지정
  python scripts/generate_changelog.py --output docs/CHANGELOG.md
        """,
    )

    parser.add_argument(
        "--since", type=str, default=None, help="시작 태그/커밋 (예: v1.0.0, HEAD~10)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="CHANGELOG.md",
        help="출력 파일 경로 (기본값: CHANGELOG.md)",
    )

    args = parser.parse_args()

    generator = ChangelogGenerator(since_tag=args.since, output_path=args.output)
    generator.generate()


if __name__ == "__main__":
    main()
