"""
Stage 4: Anomaly Detection Module

이상치 탐지 관련 기능을 제공합니다.
"""

from .anomaly_detector import main as detect_anomalies

__all__ = ["detect_anomalies"]
