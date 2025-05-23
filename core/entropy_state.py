# core/entropy_state.py

import numpy as np
import threading
import time
import logging
from typing import List, Tuple

logger = logging.getLogger("EntropyState")

class EntropyState:
    def __init__(self):
        self.current_score: float = 0.0
        self.signal_history: List[Tuple[float, float]] = []
        self.lock = threading.Lock()

    def update_entropy(self, signal_vector: np.ndarray) -> float:
        entropy = self.calculate_entropy(signal_vector)
        with self.lock:
            timestamp = time.time()
            self.signal_history.append((timestamp, entropy))
            self.current_score = entropy
        logger.debug(f"Entropy updated: {entropy:.4f}")
        return entropy

    def calculate_entropy(self, signal_vector: np.ndarray) -> float:
        if signal_vector.size == 0:
            return 0.0
        values, counts = np.unique(signal_vector, return_counts=True)
        probabilities = counts / counts.sum()
        entropy = -np.sum(probabilities * np.log2(probabilities))
        return float(entropy)

    def get_recent_entropy(self, window_seconds: int = 60) -> List[float]:
        now = time.time()
        with self.lock:
            return [e for t, e in self.signal_history if (now - t) <= window_seconds]
