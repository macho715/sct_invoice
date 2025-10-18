#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""병렬 처리 유틸리티"""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Callable, Any, Dict
import multiprocessing
import logging


class ParallelProcessor:
    """병렬 처리 헬퍼 클래스"""

    def __init__(self, max_workers=None):
        """
        Args:
            max_workers: 최대 워커 수 (None이면 최적 워커 수 계산)
        """
        if max_workers is None:
            # 최적 워커 수 계산: min(32, cpu_count * 2)
            cpu_count = multiprocessing.cpu_count()
            self.max_workers = min(32, cpu_count * 2)
        else:
            self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)

    def process_batches(
        self,
        items: List[Any],
        batch_size: int,
        process_func: Callable,
        use_threads=True,
    ) -> List[Any]:
        """
        아이템을 배치로 나누어 병렬 처리

        Args:
            items: 처리할 아이템 리스트
            batch_size: 배치 크기
            process_func: 처리 함수 (배치를 받아 결과 반환)
            use_threads: True면 ThreadPool, False면 ProcessPool

        Returns:
            처리 결과 리스트
        """
        # 배치 생성
        batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

        self.logger.info(
            f"병렬 처리 시작: {len(items)}개 아이템, "
            f"{len(batches)}개 배치, "
            f"{self.max_workers}개 워커"
        )

        # 병렬 처리
        executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor

        results = []
        with executor_class(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_func, batch): i
                for i, batch in enumerate(batches)
            }

            for future in as_completed(futures):
                batch_idx = futures[future]
                try:
                    result = future.result()
                    results.append((batch_idx, result))
                except Exception as e:
                    self.logger.error(f"배치 {batch_idx} 처리 실패: {e}")
                    raise

        # 원래 순서대로 정렬
        results.sort(key=lambda x: x[0])
        return [r for _, r in results]

    def parallel_map(
        self, func: Callable, items: List[Any], use_threads=True
    ) -> List[Any]:
        """
        각 아이템에 함수를 병렬 적용

        Args:
            func: 적용할 함수
            items: 아이템 리스트
            use_threads: True면 ThreadPool, False면 ProcessPool

        Returns:
            결과 리스트
        """
        executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            results = list(executor.map(func, items))

        return results
