# -*- coding: utf-8 -*-
"""
이상치 유형 디버깅 스크립트
"""

import json
from anomaly_detector import AnomalyType, AnomalySeverity


def debug_anomaly_types():
    """이상치 유형 디버깅"""

    # JSON 파일에서 이상치 로드
    with open("hvdc_anomaly_report_v2.json", "r", encoding="utf-8") as f:
        anomaly_data = json.load(f)

    print(f"📊 JSON에서 로드된 이상치: {len(anomaly_data)}건")

    # 이상치 유형별 분류
    type_counts = {}
    for item in anomaly_data:
        anomaly_type = item["Anomaly_Type"]
        type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1

    print(f"\n📊 이상치 유형별 분포:")
    for anomaly_type, count in type_counts.items():
        print(f"  - {anomaly_type}: {count}건")

    # AnomalyType enum 값 확인
    print(f"\n🔍 AnomalyType enum 값:")
    for anomaly_type in AnomalyType:
        print(f"  - {anomaly_type.name}: {anomaly_type.value}")

    # 처음 5개 이상치의 상세 정보
    print(f"\n🔍 처음 5개 이상치 상세 정보:")
    for i, item in enumerate(anomaly_data[:5]):
        print(f"  {i+1}. Case ID: {item['Case_ID']}")
        print(f"     - Anomaly_Type: '{item['Anomaly_Type']}'")
        print(f"     - Severity: '{item['Severity']}'")
        print(f"     - Description: {item['Description']}")
        print()


if __name__ == "__main__":
    debug_anomaly_types()
"""
이상치 유형 디버깅 스크립트
"""

import json
from anomaly_detector import AnomalyType, AnomalySeverity


def debug_anomaly_types():
    """이상치 유형 디버깅"""

    # JSON 파일에서 이상치 로드
    with open("hvdc_anomaly_report_v2.json", "r", encoding="utf-8") as f:
        anomaly_data = json.load(f)

    print(f"📊 JSON에서 로드된 이상치: {len(anomaly_data)}건")

    # 이상치 유형별 분류
    type_counts = {}
    for item in anomaly_data:
        anomaly_type = item["Anomaly_Type"]
        type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1

    print(f"\n📊 이상치 유형별 분포:")
    for anomaly_type, count in type_counts.items():
        print(f"  - {anomaly_type}: {count}건")

    # AnomalyType enum 값 확인
    print(f"\n🔍 AnomalyType enum 값:")
    for anomaly_type in AnomalyType:
        print(f"  - {anomaly_type.name}: {anomaly_type.value}")

    # 처음 5개 이상치의 상세 정보
    print(f"\n🔍 처음 5개 이상치 상세 정보:")
    for i, item in enumerate(anomaly_data[:5]):
        print(f"  {i+1}. Case ID: {item['Case_ID']}")
        print(f"     - Anomaly_Type: '{item['Anomaly_Type']}'")
        print(f"     - Severity: '{item['Severity']}'")
        print(f"     - Description: {item['Description']}")
        print()


if __name__ == "__main__":
    debug_anomaly_types()
