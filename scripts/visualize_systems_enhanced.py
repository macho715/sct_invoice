#!/usr/bin/env python3
"""
HVDC Project Enhanced System Visualization
SYSTEM GRAPH.MD의 프로급 시각화 기법을 적용한 향상된 시스템 관계도
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import networkx as nx
import numpy as np

# 한글 폰트 설정
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


class EnhancedSystemAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.data = {}
        self.analyze_project()

    def analyze_project(self):
        """프로젝트 구조 분석 (향상된 버전)"""
        print("🔍 Enhanced 프로젝트 구조 분석 중...")

        # 서브시스템 정의 (그룹별 분류)
        self.data["subsystems"] = {}
        self.data["groups"] = {
            "core": {
                "name": "Core Systems",
                "color": "#FF6B6B",
                "systems": ["HVDC_Invoice_Audit", "hitachi", "ML"],
            },
            "storage": {
                "name": "Storage & Processing",
                "color": "#4ECDC4",
                "systems": ["PDF", "hybrid_doc_system_artifacts_v1"],
            },
            "support": {
                "name": "Support",
                "color": "#96CEB4",
                "systems": ["scripts", "tests"],
            },
            "documentation": {
                "name": "Documentation",
                "color": "#FFEAA7",
                "systems": ["docs"],
            },
        }

        # 파일 분석
        for file_path in self.project_root.rglob("*"):
            try:
                if file_path.is_file() and not self._should_ignore(file_path):
                    # 서브시스템별 분석
                    for group_name, group_data in self.data["groups"].items():
                        for sys_name in group_data["systems"]:
                            if sys_name in str(file_path):
                                if sys_name not in self.data["subsystems"]:
                                    self.data["subsystems"][sys_name] = {
                                        "display_name": self._get_display_name(
                                            sys_name
                                        ),
                                        "files": 0,
                                        "group": group_name,
                                    }
                                self.data["subsystems"][sys_name]["files"] += 1
            except (OSError, PermissionError, FileNotFoundError):
                continue

        print(f"✅ 분석 완료: {len(self.data['subsystems'])}개 서브시스템")

    def _get_display_name(self, sys_name):
        """시스템 표시명 변환"""
        display_names = {
            "HVDC_Invoice_Audit": "HVDC Invoice Audit",
            "hitachi": "Hitachi Sync",
            "ML": "ML Optimization",
            "PDF": "PDF Processing",
            "hybrid_doc_system_artifacts_v1": "Hybrid Doc System",
            "scripts": "Scripts",
            "tests": "Tests",
            "docs": "Documentation",
        }
        return display_names.get(sys_name, sys_name)

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
            "*.xlsx",
            "*.xls",
            "*.pdf",
        ]

        path_str = str(file_path).lower()
        for pattern in ignore_patterns:
            if pattern.lower() in path_str or file_path.name.startswith("."):
                return True
        return False


class EnhancedSystemVisualizer:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.data = analyzer.data

    def create_enhanced_system_relationship_graph(self):
        """향상된 시스템 관계도 네트워크 그래프 생성"""
        print("📊 Enhanced 시스템 관계도 생성 중...")

        fig, ax = plt.subplots(figsize=(16, 12))
        ax.set_title(
            "HVDC Project - Enhanced System Relationships",
            fontsize=20,
            fontweight="bold",
            pad=30,
        )

        # Directed Graph 생성
        G = nx.DiGraph()

        # 노드 추가 (그룹 정보 포함)
        for sys_name, sys_data in self.data["subsystems"].items():
            G.add_node(
                sys_name,
                label=sys_data["display_name"],
                files=sys_data["files"],
                group=sys_data["group"],
            )

        # 연결 관계 정의 (실제 프로젝트 구조 기반)
        connections = [
            # Core Systems 내부 연결
            ("HVDC_Invoice_Audit", "hitachi"),
            ("HVDC_Invoice_Audit", "ML"),
            ("HVDC_Invoice_Audit", "PDF"),
            # Storage 연결
            ("PDF", "hybrid_doc_system_artifacts_v1"),
            # Support 연결
            ("hitachi", "scripts"),
            ("ML", "scripts"),
            ("PDF", "scripts"),
            ("hybrid_doc_system_artifacts_v1", "scripts"),
            # Documentation 연결
            ("docs", "HVDC_Invoice_Audit"),
            ("docs", "hitachi"),
            ("docs", "ML"),
            ("docs", "PDF"),
            # Tests 연결
            ("tests", "HVDC_Invoice_Audit"),
            ("tests", "hitachi"),
            # Scripts → Documentation
            ("scripts", "docs"),
        ]

        for source, target in connections:
            if source in G.nodes and target in G.nodes:
                G.add_edge(source, target)

        # 계층형 레이아웃 (shell_layout)
        core_nodes = [n for n, d in G.nodes(data=True) if d.get("group") == "core"]
        storage_nodes = [
            n for n, d in G.nodes(data=True) if d.get("group") == "storage"
        ]
        support_nodes = [
            n for n, d in G.nodes(data=True) if d.get("group") == "support"
        ]
        doc_nodes = [
            n for n, d in G.nodes(data=True) if d.get("group") == "documentation"
        ]

        # 계층별로 배치
        nlist = [core_nodes, storage_nodes, support_nodes, doc_nodes]
        pos = nx.shell_layout(G, nlist=nlist, scale=3)

        # 노드 크기 (파일 수에 비례)
        node_sizes = [d.get("files", 1) * 15 for n, d in G.nodes(data=True)]

        # 그룹별 색상
        node_colors = []
        for n, d in G.nodes(data=True):
            group = d.get("group", "core")
            color = self.data["groups"][group]["color"]
            node_colors.append(color)

        # 노드 그리기
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.9,
            ax=ax,
        )

        # 엣지 그리기 (화살표와 곡선)
        nx.draw_networkx_edges(
            G,
            pos,
            arrows=True,
            arrowsize=25,
            arrowstyle="->",
            connectionstyle="arc3,rad=0.1",
            edge_color="#666666",
            width=2.5,
            alpha=0.7,
            ax=ax,
        )

        # 라벨 그리기 (파일 수 포함)
        labels = {}
        for n, d in G.nodes(data=True):
            files = d.get("files", 0)
            labels[n] = f"{d['label']}\n({files} files)"

        nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight="bold", ax=ax)

        # 그룹별 범례 추가
        legend_elements = []
        for group_name, group_data in self.data["groups"].items():
            if any(d.get("group") == group_name for n, d in G.nodes(data=True)):
                legend_elements.append(
                    mpatches.Patch(color=group_data["color"], label=group_data["name"])
                )

        ax.legend(
            handles=legend_elements,
            loc="upper right",
            bbox_to_anchor=(1.15, 1),
            fontsize=12,
        )

        # 그리드 추가
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)

        # 축 제거
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)

        plt.tight_layout()
        return fig

    def create_enhanced_files_per_subsystem_chart(self):
        """향상된 서브시스템별 파일 수 차트 생성"""
        print("📊 Enhanced 파일 분포 차트 생성 중...")

        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_title(
            "HVDC Project - Enhanced Files per Subsystem",
            fontsize=18,
            fontweight="bold",
            pad=25,
        )

        # 데이터 준비 (그룹별 정렬)
        systems = []
        file_counts = []
        colors = []

        for group_name, group_data in self.data["groups"].items():
            group_systems = []
            group_counts = []

            for sys_name, sys_data in self.data["subsystems"].items():
                if sys_data["group"] == group_name:
                    group_systems.append(sys_data["display_name"])
                    group_counts.append(sys_data["files"])

            # 그룹 내에서 파일 수 기준 정렬
            if group_systems:
                sorted_pairs = sorted(
                    zip(group_systems, group_counts), key=lambda x: x[1], reverse=True
                )
                group_systems, group_counts = zip(*sorted_pairs)

                systems.extend(group_systems)
                file_counts.extend(group_counts)
                colors.extend([group_data["color"]] * len(group_systems))

        if not systems:
            ax.text(
                0.5, 0.5, "No data available", ha="center", va="center", fontsize=14
            )
            return fig

        # 수평 막대 그래프
        y_pos = np.arange(len(systems))

        bars = ax.barh(
            y_pos,
            file_counts,
            color=colors,
            alpha=0.8,
            edgecolor="white",
            linewidth=1.5,
            height=0.7,
        )

        # 값 표시
        max_count = max(file_counts) if file_counts else 1
        for i, (bar, count) in enumerate(zip(bars, file_counts)):
            ax.text(
                bar.get_width() + max_count * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{count:,}",
                va="center",
                fontweight="bold",
                fontsize=11,
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(systems, fontsize=11)
        ax.set_xlabel("Number of Files", fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3, linestyle="--")

        # 축 스타일링
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        # 그룹별 범례 추가
        legend_elements = []
        for group_name, group_data in self.data["groups"].items():
            if any(
                d.get("group") == group_name for n, d in self.data["subsystems"].items()
            ):
                legend_elements.append(
                    mpatches.Patch(color=group_data["color"], label=group_data["name"])
                )

        ax.legend(
            handles=legend_elements,
            loc="lower right",
            bbox_to_anchor=(1.0, 0.0),
            fontsize=12,
        )

        plt.tight_layout()
        return fig

    def save_enhanced_visualizations(self):
        """향상된 시각화 저장"""
        output_dir = Path("docs/visualizations")
        output_dir.mkdir(exist_ok=True)

        # Enhanced 시스템 관계도 저장
        fig1 = self.create_enhanced_system_relationship_graph()
        relationship_path = output_dir / "SYSTEM_RELATIONSHIPS_V2.png"
        fig1.savefig(
            relationship_path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close(fig1)
        print(f"✅ Enhanced 시스템 관계도 저장: {relationship_path}")

        # Enhanced 파일 분포 차트 저장
        fig2 = self.create_enhanced_files_per_subsystem_chart()
        files_path = output_dir / "FILES_PER_SUBSYSTEM_V2.png"
        fig2.savefig(
            files_path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close(fig2)
        print(f"✅ Enhanced 파일 분포 차트 저장: {files_path}")


def main():
    """메인 실행 함수"""
    print("🚀 HVDC Enhanced 시스템 시각화 시작")
    print("=" * 60)

    # 프로젝트 분석
    analyzer = EnhancedSystemAnalyzer()

    # 시각화 생성
    visualizer = EnhancedSystemVisualizer(analyzer)

    # 시각화 저장
    visualizer.save_enhanced_visualizations()

    # 결과 요약
    print("\n📊 Enhanced 분석 결과 요약:")
    print("-" * 40)

    for group_name, group_data in analyzer.data["groups"].items():
        group_systems = [
            s
            for s, d in analyzer.data["subsystems"].items()
            if d.get("group") == group_name
        ]
        if group_systems:
            print(f"\n{group_data['name']}:")
            for sys_name in group_systems:
                sys_data = analyzer.data["subsystems"][sys_name]
                print(f"  • {sys_data['display_name']}: {sys_data['files']:,}개 파일")

    print(f"\n✅ Enhanced 시각화 완료: 2개 그래프 생성")
    print("📁 저장 위치: docs/visualizations/")
    print("🎨 특징: 그룹별 색상, 방향성 화살표, 계층형 레이아웃")


if __name__ == "__main__":
    main()
