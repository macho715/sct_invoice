#!/usr/bin/env python3
"""
HVDC Project System Visualization
시스템 관계도 및 파일 분포 그래프 생성
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


class SystemAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.data = {}
        self.analyze_project()

    def analyze_project(self):
        """프로젝트 구조 분석 (간소화 버전)"""
        print("🔍 프로젝트 구조 분석 중...")

        # 기본 통계
        self.data["subsystems"] = {}

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
                    # 서브시스템별 분석
                    for sys_name, sys_display in subsystems.items():
                        if sys_name in str(file_path):
                            if sys_name not in self.data["subsystems"]:
                                self.data["subsystems"][sys_name] = {
                                    "display_name": sys_display,
                                    "files": 0,
                                }
                            self.data["subsystems"][sys_name]["files"] += 1
            except (OSError, PermissionError, FileNotFoundError):
                continue

        print(f"✅ 분석 완료: {len(self.data['subsystems'])}개 서브시스템")

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


class SystemVisualizer:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.data = analyzer.data

    def create_system_relationship_graph(self):
        """시스템 관계도 네트워크 그래프 생성"""
        print("📊 시스템 관계도 생성 중...")

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_title(
            "HVDC Project - System Relationships",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

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
            ("hybrid_doc_system_artifacts_v1", "HVDC_Invoice_Audit"),
            ("scripts", "docs"),
            ("scripts", "tests"),
        ]

        for source, target in connections:
            if source in systems and target in systems:
                G.add_edge(source, target)

        # 그래프 그리기
        pos = nx.spring_layout(G, k=4, iterations=100, seed=42)

        # 노드 색상 정의
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

        # 노드 그리기
        nx.draw_networkx_nodes(
            G,
            pos,
            node_color=node_colors[: len(systems)],
            node_size=3000,
            alpha=0.9,
            ax=ax,
        )

        # 엣지 그리기
        nx.draw_networkx_edges(G, pos, alpha=0.6, width=3, edge_color="#666666", ax=ax)

        # 라벨 그리기
        labels = {node: data["label"] for node, data in G.nodes(data=True)}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold", ax=ax)

        # 범례 추가
        legend_elements = []
        for i, (sys, data) in enumerate(self.data["subsystems"].items()):
            legend_elements.append(
                mpatches.Patch(color=node_colors[i], label=data["display_name"])
            )

        ax.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(1.15, 1))
        ax.axis("off")

        plt.tight_layout()
        return fig

    def create_files_per_subsystem_chart(self):
        """서브시스템별 파일 수 막대 그래프 생성"""
        print("📊 파일 분포 차트 생성 중...")

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_title(
            "HVDC Project - Files per Subsystem", fontsize=16, fontweight="bold", pad=20
        )

        # 데이터 준비
        systems = []
        file_counts = []

        for sys_name, sys_data in self.data["subsystems"].items():
            systems.append(sys_data["display_name"])
            file_counts.append(sys_data["files"])

        if not systems:
            ax.text(
                0.5, 0.5, "No data available", ha="center", va="center", fontsize=14
            )
            return fig

        # 파일 수 기준 정렬 (내림차순)
        sorted_data = sorted(
            zip(systems, file_counts), key=lambda x: x[1], reverse=True
        )
        systems, file_counts = zip(*sorted_data)

        # 수평 막대 그래프
        y_pos = np.arange(len(systems))
        colors = plt.cm.viridis(np.linspace(0, 1, len(systems)))

        bars = ax.barh(
            y_pos, file_counts, color=colors, alpha=0.8, edgecolor="white", linewidth=1
        )

        # 값 표시
        for i, (bar, count) in enumerate(zip(bars, file_counts)):
            ax.text(
                bar.get_width() + max(file_counts) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                str(count),
                va="center",
                fontweight="bold",
                fontsize=11,
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(systems, fontsize=11)
        ax.set_xlabel("Number of Files", fontsize=12, fontweight="bold")
        ax.grid(axis="x", alpha=0.3, linestyle="--")

        # 축 스타일링
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(0.5)
        ax.spines["bottom"].set_linewidth(0.5)

        plt.tight_layout()
        return fig

    def save_visualizations(self):
        """시각화 저장"""
        output_dir = Path("docs/visualizations")
        output_dir.mkdir(exist_ok=True)

        # 시스템 관계도 저장
        fig1 = self.create_system_relationship_graph()
        relationship_path = output_dir / "SYSTEM_RELATIONSHIPS.png"
        fig1.savefig(
            relationship_path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close(fig1)
        print(f"✅ 시스템 관계도 저장: {relationship_path}")

        # 파일 분포 차트 저장
        fig2 = self.create_files_per_subsystem_chart()
        files_path = output_dir / "FILES_PER_SUBSYSTEM.png"
        fig2.savefig(
            files_path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        plt.close(fig2)
        print(f"✅ 파일 분포 차트 저장: {files_path}")


def main():
    """메인 실행 함수"""
    print("🚀 HVDC 시스템 시각화 시작")
    print("=" * 50)

    # 프로젝트 분석
    analyzer = SystemAnalyzer()

    # 시각화 생성
    visualizer = SystemVisualizer(analyzer)

    # 시각화 저장
    visualizer.save_visualizations()

    # 결과 요약
    print("\n📊 분석 결과 요약:")
    print("-" * 30)
    for sys_name, sys_data in analyzer.data["subsystems"].items():
        print(f"  {sys_data['display_name']}: {sys_data['files']}개 파일")

    print(f"\n✅ 시각화 완료: 2개 그래프 생성")
    print("📁 저장 위치: docs/visualizations/")


if __name__ == "__main__":
    main()
