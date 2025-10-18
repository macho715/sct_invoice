#!/usr/bin/env python3
"""
HVDC Project Overview Visualization Dashboard
프로젝트 전체 구조를 다양한 그래프로 시각화
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict, Counter
import networkx as nx
import squarify
import numpy as np
from datetime import datetime

# 한글 폰트 설정
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


class ProjectAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.data = {}
        self.analyze_project()

    def analyze_project(self):
        """프로젝트 구조 분석"""
        print("🔍 프로젝트 구조 분석 중...")

        # 기본 통계
        self.data["total_files"] = 0
        self.data["total_lines"] = 0
        self.data["file_types"] = defaultdict(int)
        self.data["folder_structure"] = defaultdict(int)
        self.data["subsystems"] = {}
        self.data["documentation"] = {}

        # 주요 서브시스템 정의
        subsystems = {
            "HVDC_Invoice_Audit": "HVDC Invoice Audit",
            "hitachi": "Hitachi Sync System",
            "ML": "ML Optimization",
            "PDF": "PDF Processing",
            "hybrid_doc_system_artifacts_v1": "Hybrid Doc System",
            "scripts": "Scripts",
            "docs": "Documentation",
            "tests": "Tests",
        }

        # 파일 분석
        for file_path in self.project_root.rglob("*"):
            try:
                if file_path.is_file() and not self._should_ignore(file_path):
                    self.data["total_files"] += 1

                    # 파일 타입 분석
                    ext = file_path.suffix.lower()
                    if ext in [".py"]:
                        self.data["file_types"]["Python"] += 1
                        self.data["total_lines"] += self._count_lines(file_path)
                    elif ext in [".xlsx", ".xls"]:
                        self.data["file_types"]["Excel"] += 1
                    elif ext in [".md"]:
                        self.data["file_types"]["Markdown"] += 1
                    elif ext in [".json", ".yaml", ".yml"]:
                        self.data["file_types"]["Config"] += 1
                    else:
                        self.data["file_types"]["Other"] += 1

                    # 폴더별 파일 수
                    folder = file_path.parent.name
                    self.data["folder_structure"][folder] += 1

                    # 서브시스템별 분석
                    for sys_name, sys_display in subsystems.items():
                        if sys_name in str(file_path):
                            if sys_name not in self.data["subsystems"]:
                                self.data["subsystems"][sys_name] = {
                                    "display_name": sys_display,
                                    "files": 0,
                                    "lines": 0,
                                    "has_readme": False,
                                    "has_architecture": False,
                                    "has_plan": False,
                                    "has_guide": False,
                                }
                            self.data["subsystems"][sys_name]["files"] += 1
                            if ext == ".py":
                                self.data["subsystems"][sys_name][
                                    "lines"
                                ] += self._count_lines(file_path)
            except (OSError, PermissionError, FileNotFoundError):
                # 접근할 수 없는 파일은 무시
                continue

        # 문서화 현황 분석
        self._analyze_documentation()

        print(
            f"✅ 분석 완료: {self.data['total_files']}개 파일, {self.data['total_lines']:,}줄"
        )

    def _should_ignore(self, file_path):
        """무시할 파일/폴더 판단"""
        ignore_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "venv",
            "env",
            ".vscode",
            ".idea",
            "node_modules",
            ".backup",
            "*.pyc",
            "*.log",
            "*.cache",
            "lib64",
            "lib",
            "include",
            "Scripts",
            "site-packages",
            ".gitignore",
        ]

        path_str = str(file_path).lower()
        for pattern in ignore_patterns:
            if pattern.lower() in path_str or file_path.name.startswith("."):
                return True
        return False

    def _count_lines(self, file_path):
        """파일 라인 수 계산"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return len(f.readlines())
        except:
            return 0

    def _analyze_documentation(self):
        """문서화 현황 분석"""
        doc_indicators = {
            "README": ["README.md", "readme.md"],
            "Architecture": ["ARCHITECTURE.md", "SYSTEM_ARCHITECTURE.md"],
            "Plan": ["plan.md", "PLAN.md"],
            "Guide": ["guide.md", "GUIDE.md", "DEPLOYMENT_GUIDE.md"],
        }

        for sys_name in self.data["subsystems"]:
            sys_path = self.project_root / sys_name
            if sys_path.exists():
                for doc_type, patterns in doc_indicators.items():
                    for pattern in patterns:
                        if (sys_path / pattern).exists():
                            self.data["subsystems"][sys_name][
                                f"has_{doc_type.lower()}"
                            ] = True
                            break


class ProjectVisualizer:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.data = analyzer.data

    def create_dashboard(self):
        """전체 대시보드 생성"""
        print("📊 대시보드 생성 중...")

        fig = plt.figure(figsize=(20, 12))
        fig.suptitle(
            "HVDC Project Overview Dashboard", fontsize=20, fontweight="bold", y=0.95
        )

        # 6개 서브플롯 배치
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # 1. 트리맵 (폴더 구조)
        ax1 = fig.add_subplot(gs[0, 0])
        self._create_treemap(ax1)

        # 2. 시스템 관계도
        ax2 = fig.add_subplot(gs[0, 1])
        self._create_relationship_graph(ax2)

        # 3. 파일 타입 분포
        ax3 = fig.add_subplot(gs[1, 0])
        self._create_file_type_pie(ax3)

        # 4. 서브시스템 파일 수
        ax4 = fig.add_subplot(gs[1, 1])
        self._create_subsystem_bar(ax4)

        # 5. 문서화 현황
        ax5 = fig.add_subplot(gs[2, 0])
        self._create_documentation_gauge(ax5)

        # 6. 주요 메트릭
        ax6 = fig.add_subplot(gs[2, 1])
        self._create_metrics_table(ax6)

        plt.tight_layout()
        return fig

    def _create_treemap(self, ax):
        """폴더 구조 트리맵"""
        ax.set_title("Project Folder Structure (Treemap)", fontweight="bold")

        # 폴더별 파일 수 데이터 준비
        folders = list(self.data["folder_structure"].keys())
        sizes = list(self.data["folder_structure"].values())

        if not folders:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            return

        # 색상 매핑
        colors = plt.cm.Set3(np.linspace(0, 1, len(folders)))

        # 트리맵 생성
        squarify.plot(sizes=sizes, label=folders, color=colors, ax=ax, alpha=0.8)
        ax.axis("off")

    def _create_relationship_graph(self, ax):
        """시스템 간 관계도"""
        ax.set_title("System Relationships (Network Graph)", fontweight="bold")

        G = nx.Graph()

        # 노드 추가
        systems = list(self.data["subsystems"].keys())
        for sys in systems:
            G.add_node(sys, label=self.data["subsystems"][sys]["display_name"])

        # 연결 관계 정의 (실제 프로젝트 구조 기반)
        connections = [
            ("HVDC_Invoice_Audit", "hitachi"),
            ("HVDC_Invoice_Audit", "ML"),
            ("HVDC_Invoice_Audit", "PDF"),
            ("hitachi", "scripts"),
            ("ML", "scripts"),
            ("PDF", "scripts"),
            ("docs", "HVDC_Invoice_Audit"),
            ("docs", "hitachi"),
            ("docs", "ML"),
            ("docs", "PDF"),
            ("tests", "HVDC_Invoice_Audit"),
            ("tests", "hitachi"),
        ]

        for source, target in connections:
            if source in systems and target in systems:
                G.add_edge(source, target)

        # 그래프 그리기
        pos = nx.spring_layout(G, k=3, iterations=50)

        # 노드 그리기
        node_colors = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#96CEB4",
            "#FFEAA7",
            "#DDA0DD",
            "#98D8C8",
            "#F7DC6F",
        ]
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color=node_colors[: len(systems)],
            node_size=2000,
            alpha=0.8,
            ax=ax,
        )

        # 엣지 그리기
        nx.draw_networkx_edges(G, pos, alpha=0.5, width=2, ax=ax)

        # 라벨 그리기
        labels = {node: data["label"] for node, data in G.nodes(data=True)}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)

        ax.axis("off")

    def _create_file_type_pie(self, ax):
        """파일 타입 분포 파이 차트"""
        ax.set_title("File Type Distribution", fontweight="bold")

        types = list(self.data["file_types"].keys())
        sizes = list(self.data["file_types"].values())
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=types,
            colors=colors[: len(types)],
            autopct="%1.1f%%",
            startangle=90,
        )

        # 라벨 스타일링
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")

    def _create_subsystem_bar(self, ax):
        """서브시스템별 파일 수 막대 그래프"""
        ax.set_title("Files per Subsystem", fontweight="bold")

        systems = []
        file_counts = []

        for sys_name, sys_data in self.data["subsystems"].items():
            systems.append(sys_data["display_name"])
            file_counts.append(sys_data["files"])

        if not systems:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            return

        # 수평 막대 그래프
        y_pos = np.arange(len(systems))
        colors = plt.cm.viridis(np.linspace(0, 1, len(systems)))

        bars = ax.barh(y_pos, file_counts, color=colors, alpha=0.8)

        # 값 표시
        for i, (bar, count) in enumerate(zip(bars, file_counts)):
            ax.text(
                bar.get_width() + 0.1,
                bar.get_y() + bar.get_height() / 2,
                str(count),
                va="center",
                fontweight="bold",
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(systems, fontsize=9)
        ax.set_xlabel("Number of Files")
        ax.grid(axis="x", alpha=0.3)

    def _create_documentation_gauge(self, ax):
        """문서화 현황 게이지"""
        ax.set_title("Documentation Status", fontweight="bold")

        # 문서화 지표 계산
        total_systems = len(self.data["subsystems"])
        if total_systems == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            return

        readme_count = sum(
            1 for sys in self.data["subsystems"].values() if sys["has_readme"]
        )
        arch_count = sum(
            1 for sys in self.data["subsystems"].values() if sys["has_architecture"]
        )
        plan_count = sum(
            1 for sys in self.data["subsystems"].values() if sys["has_plan"]
        )
        guide_count = sum(
            1 for sys in self.data["subsystems"].values() if sys["has_guide"]
        )

        # 막대 차트로 변경
        categories = ["README", "Architecture", "Plan", "Guide"]
        counts = [readme_count, arch_count, plan_count, guide_count]
        percentages = [count / total_systems * 100 for count in counts]

        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]

        # 수평 막대 차트
        y_pos = np.arange(len(categories))
        bars = ax.barh(y_pos, percentages, color=colors, alpha=0.8)

        # 값 표시
        for i, (bar, pct, count) in enumerate(zip(bars, percentages, counts)):
            ax.text(
                bar.get_width() + 1,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.0f}% ({count}/{total_systems})",
                va="center",
                fontweight="bold",
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories)
        ax.set_xlabel("Documentation Coverage (%)")
        ax.set_xlim(0, 100)
        ax.grid(axis="x", alpha=0.3)

    def _create_metrics_table(self, ax):
        """주요 메트릭 테이블"""
        ax.set_title("Key Project Metrics", fontweight="bold")
        ax.axis("off")

        # 메트릭 데이터
        metrics = [
            ("Total Files", f"{self.data['total_files']:,}"),
            ("Total Lines of Code", f"{self.data['total_lines']:,}"),
            ("Python Files", f"{self.data['file_types']['Python']:,}"),
            ("Excel Files", f"{self.data['file_types']['Excel']:,}"),
            ("Markdown Files", f"{self.data['file_types']['Markdown']:,}"),
            ("Config Files", f"{self.data['file_types']['Config']:,}"),
            ("Subsystems", f"{len(self.data['subsystems'])}"),
            ("Documentation Rate", f"{self._calc_doc_rate():.1f}%"),
        ]

        # 테이블 생성
        table_data = []
        for metric, value in metrics:
            table_data.append([metric, value])

        table = ax.table(
            cellText=table_data,
            colLabels=["Metric", "Value"],
            cellLoc="left",
            loc="center",
            bbox=[0, 0, 1, 1],
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)

        # 헤더 스타일링
        for i in range(2):
            table[(0, i)].set_facecolor("#4ECDC4")
            table[(0, i)].set_text_props(weight="bold", color="white")

        # 데이터 셀 스타일링
        for i in range(1, len(table_data) + 1):
            for j in range(2):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor("#F8F9FA")

    def _calc_doc_rate(self):
        """문서화 비율 계산"""
        total_systems = len(self.data["subsystems"])
        if total_systems == 0:
            return 0

        documented = sum(
            1
            for sys in self.data["subsystems"].values()
            if any(
                [
                    sys["has_readme"],
                    sys["has_architecture"],
                    sys["has_plan"],
                    sys["has_guide"],
                ]
            )
        )
        return (documented / total_systems) * 100


def main():
    """메인 실행 함수"""
    print("🚀 HVDC Project Overview Visualization 시작")
    print("=" * 50)

    # 프로젝트 분석
    analyzer = ProjectAnalyzer()

    # 시각화 생성
    visualizer = ProjectVisualizer(analyzer)

    # 대시보드 생성
    fig = visualizer.create_dashboard()

    # 저장
    output_dir = Path("docs/visualizations")
    output_dir.mkdir(exist_ok=True)

    dashboard_path = output_dir / "PROJECT_OVERVIEW_DASHBOARD.png"
    fig.savefig(
        dashboard_path,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    print(f"✅ 대시보드 저장 완료: {dashboard_path}")
    print(
        f"📊 총 {analyzer.data['total_files']}개 파일, {analyzer.data['total_lines']:,}줄 분석"
    )
    print(f"📁 {len(analyzer.data['subsystems'])}개 서브시스템 식별")
    print(f"📚 문서화 비율: {visualizer._calc_doc_rate():.1f}%")

    plt.show()


if __name__ == "__main__":
    main()
