# core/entropy_feedback_loop.py

import numpy as np
import threading
import time
import random
import logging
import traceback
from typing import Optional, List, Tuple

from core.signal_reforge import SignalReforger
from core.reality_mutator import inject_protocol_drift
from core.entropy_state import EntropyState

# ─────────────────────────────────────────────
# Defensive ML model loader fallback
# ─────────────────────────────────────────────
try:
    from modules.ml_models.model_loader import load_adversarial_model
except ImportError:
    def load_adversarial_model():
        logging.warning("[ML] No adversarial model loaded (modules.ml_models.model_loader missing)")
        return None

logger = logging.getLogger("EntropyFeedback")
logger.setLevel(logging.DEBUG)


class EntropyState:
    """
    Tracks entropy trends of RF-like signals and maintains a historical window.
    """

    def __init__(self):
        self.current_score: float = 0.0
        self.signal_history: List[Tuple[float, float]] = []
        self.lock = threading.Lock()
        self.model = load_adversarial_model()

    def calculate_entropy(self, signal: np.ndarray) -> float:
        """
        Shannon entropy based on discrete signal values.
        """
        if signal.size == 0:
            return 0.0
        values, counts = np.unique(signal, return_counts=True)
        probabilities = counts / counts.sum()
        entropy = -np.sum(probabilities * np.log2(probabilities))
        return float(entropy)

    def update_entropy(self, signal_vector: np.ndarray) -> float:
        entropy = self.calculate_entropy(signal_vector)
        with self.lock:
            timestamp = time.time()
            self.signal_history.append((timestamp, entropy))
            self.current_score = entropy
        logger.debug(f"[Entropy] Updated score: {entropy:.4f}")
        return entropy

    def get_recent_entropy(self, window_seconds: int = 60) -> List[float]:
        now = time.time()
        with self.lock:
            return [e for t, e in self.signal_history if (now - t) <= window_seconds]


class EntropyFeedbackLoop:
    """
    Adaptive controller that reacts to entropy delta trends and emits attack triggers.
    """

    def __init__(self, feedback_interval: int = 10, entropy_threshold: float = 6.0):
        self.state = EntropyState()
        self.feedback_interval = feedback_interval
        self.entropy_threshold = entropy_threshold
        self.running = False
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.reforger = SignalReforger(simulation=True)

    def start(self):
        self.running = True
        self.thread.start()
        logger.info("[Loop] Entropy feedback loop started.")

    def stop(self):
        self.running = False
        logger.info("[Loop] Entropy feedback loop stopped.")

    def _run_loop(self):
        """
        Periodically simulate a mutated signal, compute entropy, and trigger chained actions.
        """
        while self.running:
            try:
                raw_signal = self._simulate_signal_capture()
                reforged_flowgraph = self.reforger.generate_stealth_signal(raw_signal, target_entropy=0.8)

                if reforged_flowgraph is not None:
                    logger.debug("[Flowgraph] Generated in simulation mode (not executed)")

                mutated_signal = inject_protocol_drift(raw_signal)

                entropy_score = self.state.update_entropy(mutated_signal)

                if entropy_score >= self.entropy_threshold:
                    logger.info(f"[Trigger] Entropy threshold exceeded: {entropy_score:.2f}")
                    logger.info("[Trigger] (No ML chain triggered - model not configured)")

                time.sleep(self.feedback_interval)

            except Exception as ex:
                logger.error(f"[FeedbackLoop] Exception: {ex}")
                logger.debug(traceback.format_exc())
                time.sleep(self.feedback_interval)

    def _simulate_signal_capture(self) -> np.ndarray:
        """
        Return synthetic 8-bit signal burst to emulate intercepted RF block.
        """
        return np.random.randint(0, 256, size=1024).astype(np.uint8)

    def get_entropy_statistics(self) -> dict:
        """
        Summarize entropy trends for telemetry.
        """
        values = self.state.get_recent_entropy(window_seconds=300)
        if not values:
            return {
                "count": 0,
                "average": 0.0,
                "max": 0.0,
                "min": 0.0
            }
        return {
            "count": len(values),
            "average": float(np.mean(values)),
            "max": float(np.max(values)),
            "min": float(np.min(values))
        }


# ─────────────────────────────────────────────
# CLI testing (manual standalone execution)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    loop = EntropyFeedbackLoop(feedback_interval=5, entropy_threshold=6.0)
    try:
        loop.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        loop.stop()
