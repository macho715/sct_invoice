#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vectorized Batch Processing System
벡터화 연산을 활용한 고성능 배치 처리
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Callable
from functools import lru_cache
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from error_handling import LoggerManager, ProgressLogger, handle_errors

logger = LoggerManager().get_logger(__name__)


class VectorizedSimilarity:
    """
    벡터화된 유사도 계산
    
    Features:
    - NumPy 벡터 연산 활용
    - 배치 처리 최적화
    - 캐싱 지원
    """
    
    def __init__(self, cache_size: int = 1000):
        """
        초기화
        
        Args:
            cache_size: LRU 캐시 크기
        """
        self.cache_size = cache_size
        self._clear_cache()
    
    def _clear_cache(self):
        """캐시 초기화"""
        self.token_set_similarity = lru_cache(maxsize=self.cache_size)(
            self._token_set_similarity_impl
        )
        self.levenshtein_similarity = lru_cache(maxsize=self.cache_size)(
            self._levenshtein_similarity_impl
        )
    
    @staticmethod
    def _token_set_similarity_impl(s1: str, s2: str) -> float:
        """Token set 유사도 (Jaccard)"""
        if not s1 or not s2:
            return 0.0
        
        tokens1 = set(str(s1).upper().split())
        tokens2 = set(str(s2).upper().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def _levenshtein_similarity_impl(s1: str, s2: str) -> float:
        """Levenshtein 유사도 (정규화)"""
        if not s1 or not s2:
            return 0.0
        
        s1, s2 = str(s1).upper(), str(s2).upper()
        
        if s1 == s2:
            return 1.0
        
        # 간단한 character overlap 유사도 (빠른 근사)
        set1, set2 = set(s1), set(s2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def fuzzy_sort_similarity(s1: str, s2: str) -> float:
        """Fuzzy sort 유사도"""
        if not s1 or not s2:
            return 0.0
        
        # 단어 정렬 후 비교
        sorted1 = ' '.join(sorted(str(s1).upper().split()))
        sorted2 = ' '.join(sorted(str(s2).upper().split()))
        
        return 1.0 if sorted1 == sorted2 else VectorizedSimilarity._levenshtein_similarity_impl(sorted1, sorted2)
    
    def batch_similarity(
        self,
        sources: List[str],
        targets: List[str],
        weights: Dict[str, float]
    ) -> np.ndarray:
        """
        배치 유사도 계산 (벡터화)
        
        Args:
            sources: 소스 문자열 리스트
            targets: 타겟 문자열 리스트  
            weights: 가중치 딕셔너리
        
        Returns:
            유사도 행렬 (n_sources x n_targets)
        """
        n_sources = len(sources)
        n_targets = len(targets)
        
        # 결과 행렬 초기화
        token_set_scores = np.zeros((n_sources, n_targets))
        levenshtein_scores = np.zeros((n_sources, n_targets))
        fuzzy_sort_scores = np.zeros((n_sources, n_targets))
        
        # 벡터화된 계산
        for i, source in enumerate(sources):
            for j, target in enumerate(targets):
                token_set_scores[i, j] = self.token_set_similarity(source, target)
                levenshtein_scores[i, j] = self.levenshtein_similarity(source, target)
                fuzzy_sort_scores[i, j] = self.fuzzy_sort_similarity(source, target)
        
        # 가중치 적용 (벡터 연산)
        hybrid_scores = (
            token_set_scores * weights['token_set'] +
            levenshtein_scores * weights['levenshtein'] +
            fuzzy_sort_scores * weights['fuzzy_sort']
        )
        
        return hybrid_scores
    
    def find_best_matches_vectorized(
        self,
        sources: List[str],
        targets: List[str],
        weights: Dict[str, float],
        threshold: float = 0.65
    ) -> List[Tuple[int, float]]:
        """
        최적 매칭 찾기 (벡터화)
        
        Args:
            sources: 소스 문자열 리스트
            targets: 타겟 문자열 리스트
            weights: 가중치 딕셔너리
            threshold: 매칭 임계값
        
        Returns:
            각 소스에 대한 (최적 타겟 인덱스, 유사도) 리스트
        """
        # 유사도 행렬 계산
        similarity_matrix = self.batch_similarity(sources, targets, weights)
        
        # 각 소스에 대해 최대 유사도 타겟 찾기 (벡터 연산)
        best_indices = np.argmax(similarity_matrix, axis=1)
        best_scores = np.max(similarity_matrix, axis=1)
        
        # 임계값 이하 필터링
        results = []
        for i, (idx, score) in enumerate(zip(best_indices, best_scores)):
            if score >= threshold:
                results.append((int(idx), float(score)))
            else:
                results.append((-1, 0.0))  # No match
        
        return results


class BatchProcessor:
    """
    고성능 배치 처리 시스템
    
    Features:
    - 청크 단위 처리
    - 병렬 처리 지원
    - 진행률 추적
    - 메모리 효율적 처리
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        n_workers: int = 4,
        use_multiprocessing: bool = False
    ):
        """
        초기화
        
        Args:
            chunk_size: 청크 크기
            n_workers: 병렬 워커 수
            use_multiprocessing: 멀티프로세싱 사용 여부 (False면 멀티스레딩)
        """
        self.chunk_size = chunk_size
        self.n_workers = n_workers
        self.use_multiprocessing = use_multiprocessing
    
    @handle_errors(default_return=pd.DataFrame(), raise_on_error=False)
    def process_dataframe(
        self,
        df: pd.DataFrame,
        process_func: Callable,
        show_progress: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """
        DataFrame 배치 처리
        
        Args:
            df: 처리할 DataFrame
            process_func: 각 청크에 적용할 함수
            show_progress: 진행률 표시 여부
            **kwargs: process_func에 전달할 추가 인자
        
        Returns:
            처리된 DataFrame
        """
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return df
        
        # 청크 분할
        chunks = [df[i:i+self.chunk_size] for i in range(0, len(df), self.chunk_size)]
        n_chunks = len(chunks)
        
        logger.info(f"Processing {len(df)} rows in {n_chunks} chunks of size {self.chunk_size}")
        
        # 진행률 추적
        progress = ProgressLogger(n_chunks, "Batch Processing") if show_progress else None
        
        # 병렬 처리
        executor_class = ProcessPoolExecutor if self.use_multiprocessing else ThreadPoolExecutor
        
        results = []
        with executor_class(max_workers=self.n_workers) as executor:
            futures = [executor.submit(process_func, chunk, **kwargs) for chunk in chunks]
            
            for future in futures:
                try:
                    result = future.result(timeout=300)  # 5분 타임아웃
                    results.append(result)
                    if progress:
                        progress.update(1)
                except Exception as e:
                    logger.error(f"Chunk processing failed: {e}")
                    results.append(pd.DataFrame())  # 빈 DataFrame 추가
        
        if progress:
            progress.finish()
        
        # 결과 병합
        if results:
            return pd.concat(results, ignore_index=True)
        return pd.DataFrame()
    
    def batch_match_lanes(
        self,
        invoice_df: pd.DataFrame,
        approved_lanes: List[Dict],
        weights: Dict[str, float],
        similarity_threshold: float = 0.65
    ) -> pd.DataFrame:
        """
        배치 레인 매칭 (벡터화)
        
        Args:
            invoice_df: 송장 DataFrame
            approved_lanes: 승인된 레인 리스트
            weights: 유사도 가중치
            similarity_threshold: 매칭 임계값
        
        Returns:
            매칭 결과가 추가된 DataFrame
        """
        start_time = time.time()
        
        # 빈 결과 컬럼 초기화
        invoice_df['matched_lane_index'] = -1
        invoice_df['match_score'] = 0.0
        invoice_df['match_level'] = 'NO_MATCH'
        
        # Origin-Destination 조합 추출
        origins = invoice_df['Origin'].fillna('').astype(str).str.upper().tolist()
        destinations = invoice_df['Destination'].fillna('').astype(str).str.upper().tolist()
        
        # Lane origin-destination 추출
        lane_origins = [lane.get('origin', '').upper() for lane in approved_lanes]
        lane_destinations = [lane.get('destination', '').upper() for lane in approved_lanes]
        
        # 벡터화된 유사도 계산기
        vectorized_sim = VectorizedSimilarity()
        
        logger.info(f"Computing similarities for {len(origins)} invoices against {len(lane_origins)} lanes")
        
        # Origin 유사도 계산 (벡터화)
        origin_similarity = vectorized_sim.batch_similarity(origins, lane_origins, weights)
        
        # Destination 유사도 계산 (벡터화)
        dest_similarity = vectorized_sim.batch_similarity(destinations, lane_destinations, weights)
        
        # 전체 유사도 계산 (origin 60% + destination 40%)
        total_similarity = 0.6 * origin_similarity + 0.4 * dest_similarity
        
        # 각 송장에 대해 최적 레인 찾기 (벡터 연산)
        best_lane_indices = np.argmax(total_similarity, axis=1)
        best_scores = np.max(total_similarity, axis=1)
        
        # 결과 적용 (벡터 연산)
        mask = best_scores >= similarity_threshold
        invoice_df.loc[mask, 'matched_lane_index'] = best_lane_indices[mask]
        invoice_df.loc[mask, 'match_score'] = best_scores[mask]
        invoice_df.loc[mask, 'match_level'] = 'SIMILARITY_ML'
        
        # 통계
        match_rate = mask.sum() / len(invoice_df) * 100
        elapsed = time.time() - start_time
        
        logger.info(
            f"Batch matching completed in {elapsed:.2f}s | "
            f"Match rate: {match_rate:.1f}% ({mask.sum()}/{len(invoice_df)})"
        )
        
        return invoice_df


class FeatureVectorizer:
    """
    특징 벡터화 (ML 학습용)
    
    Features:
    - 문자열 특징 벡터화
    - 수치 특징 정규화
    - 배치 처리 최적화
    """
    
    def __init__(self):
        self.vectorized_sim = VectorizedSimilarity()
    
    def compute_features_batch(
        self,
        df: pd.DataFrame,
        origin_col: str = 'origin_invoice',
        dest_col: str = 'dest_invoice',
        vehicle_col: str = 'vehicle_invoice',
        lane_origin_col: str = 'origin_lane',
        lane_dest_col: str = 'dest_lane',
        lane_vehicle_col: str = 'vehicle_lane'
    ) -> pd.DataFrame:
        """
        배치 특징 계산 (벡터화)
        
        Args:
            df: 입력 DataFrame
            origin_col: Origin 컬럼명
            dest_col: Destination 컬럼명
            vehicle_col: Vehicle 컬럼명
            lane_origin_col: Lane origin 컬럼명
            lane_dest_col: Lane destination 컬럼명
            lane_vehicle_col: Lane vehicle 컬럼명
        
        Returns:
            특징이 추가된 DataFrame
        """
        logger.info(f"Computing features for {len(df)} samples")
        
        # 벡터 추출
        origins = df[origin_col].fillna('').astype(str).tolist()
        destinations = df[dest_col].fillna('').astype(str).tolist()
        vehicles = df[vehicle_col].fillna('').astype(str).tolist()
        
        lane_origins = df[lane_origin_col].fillna('').astype(str).tolist()
        lane_destinations = df[lane_dest_col].fillna('').astype(str).tolist()
        lane_vehicles = df[lane_vehicle_col].fillna('').astype(str).tolist()
        
        # 특징 계산 (벡터화)
        n_samples = len(df)
        
        # Origin 특징
        origin_token_set = np.array([
            self.vectorized_sim.token_set_similarity(origins[i], lane_origins[i])
            for i in range(n_samples)
        ])
        origin_levenshtein = np.array([
            self.vectorized_sim.levenshtein_similarity(origins[i], lane_origins[i])
            for i in range(n_samples)
        ])
        origin_fuzzy = np.array([
            self.vectorized_sim.fuzzy_sort_similarity(origins[i], lane_origins[i])
            for i in range(n_samples)
        ])
        
        # Destination 특징
        dest_token_set = np.array([
            self.vectorized_sim.token_set_similarity(destinations[i], lane_destinations[i])
            for i in range(n_samples)
        ])
        dest_levenshtein = np.array([
            self.vectorized_sim.levenshtein_similarity(destinations[i], lane_destinations[i])
            for i in range(n_samples)
        ])
        dest_fuzzy = np.array([
            self.vectorized_sim.fuzzy_sort_similarity(destinations[i], lane_destinations[i])
            for i in range(n_samples)
        ])
        
        # 전체 특징 계산 (origin 60% + destination 40%)
        df['token_set'] = 0.6 * origin_token_set + 0.4 * dest_token_set
        df['levenshtein'] = 0.6 * origin_levenshtein + 0.4 * dest_levenshtein
        df['fuzzy_sort'] = 0.6 * origin_fuzzy + 0.4 * dest_fuzzy
        
        logger.info("Feature computation completed")
        
        return df


if __name__ == "__main__":
    # 테스트
    print("=== Vectorized Batch Processing Test ===\n")
    
    # 1. 벡터화된 유사도 테스트
    print("1. Vectorized Similarity Test")
    vectorized_sim = VectorizedSimilarity()
    
    sources = ["DSV Mussafah Yard", "Jebel Ali Port", "Abu Dhabi Port"]
    targets = ["DSV MUSSAFAH YARD", "JEBEL ALI", "ABU DHABI TERMINAL"]
    weights = {'token_set': 0.45, 'levenshtein': 0.25, 'fuzzy_sort': 0.30}
    
    similarity_matrix = vectorized_sim.batch_similarity(sources, targets, weights)
    print(f"Similarity matrix shape: {similarity_matrix.shape}")
    print(f"Sample similarities:\n{similarity_matrix}\n")
    
    # 2. 배치 매칭 테스트
    print("2. Batch Matching Test")
    matches = vectorized_sim.find_best_matches_vectorized(sources, targets, weights, threshold=0.65)
    for i, (idx, score) in enumerate(matches):
        if idx >= 0:
            print(f"  {sources[i]} -> {targets[idx]} (score: {score:.3f})")
        else:
            print(f"  {sources[i]} -> NO MATCH")
    
    # 3. DataFrame 배치 처리 테스트
    print("\n3. DataFrame Batch Processing Test")
    test_df = pd.DataFrame({
        'Origin': ['DSV Yard'] * 100,
        'Destination': ['Mirfa Site'] * 100
    })
    
    processor = BatchProcessor(chunk_size=25, n_workers=2)
    
    def dummy_process(chunk):
        chunk['processed'] = True
        return chunk
    
    result = processor.process_dataframe(test_df, dummy_process, show_progress=True)
    print(f"Processed {len(result)} rows\n")
    
    print("✅ All tests completed!")
