import os
import logging
import hashlib
import random
import numpy as np
from typing import Optional
from scipy.signal import resample

logger = logging.getLogger("SignalReforge")


class SignalReforger:
    """
    Reconstructs, modulates, and optionally transmits entropy-morphed RF signals.
    Safe to import in systems without GNU Radio or SDR support.
    """

    def __init__(self, sample_rate: float = 2e6, simulation: bool = True):
        self.sample_rate = sample_rate
        self.simulation = simulation
        self.rf_available = self._check_gnuradio()

    def _check_gnuradio(self) -> bool:
        """
        Runtime check for GNURadio and osmosdr availability.
        """
        try:
            import gnuradio.gr
            import gnuradio.osmosdr
            return True
        except ImportError:
            logger.warning("GNURadio or osmosdr not available. RF functionality disabled.")
            return False

    def apply_entropy_shift(self, signal: np.ndarray, level: float = 0.7) -> np.ndarray:
        """
        Mutate input signal using Gaussian noise to increase entropy.
        """
        mutation_mask = np.random.normal(0, level, signal.shape)
        mutated = signal + mutation_mask
        return mutated.astype(np.float32)

    def inject_jitter(self, signal: np.ndarray, jitter_ms: int = 10) -> np.ndarray:
        """
        Simulate timing anomalies by jittering signal length.
        """
        new_length = len(signal) + random.randint(-jitter_ms, jitter_ms)
        return resample(signal, max(1, new_length))

    def fingerprint_signal(self, signal: np.ndarray) -> str:
        """
        Hash signal bytes with SHA-256 for correlation.
        """
        return hashlib.sha256(signal.tobytes()).hexdigest()

    def measure_entropy(self, signal: np.ndarray) -> float:
        """
        Estimate signal entropy based on Shannon index.
        """
        values, counts = np.unique(signal, return_counts=True)
        probabilities = counts / counts.sum()
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-9))
        return float(entropy)

    def forge_modulated_flowgraph(
        self,
        signal: np.ndarray,
        modulation: str = "GFSK",
        center_freq: float = 2.437e9,
        gain: int = 20
    ) -> Optional[object]:
        """
        Build and return GNU Radio flowgraph for emission.
        """
        if self.simulation:
            logger.info("[Simulation] SDR emission skipped.")
            return None

        if not self.rf_available:
            logger.error("GNURadio + osmosdr not available. Cannot build RF flowgraph.")
            return None

        try:
            from gnuradio import gr, blocks, digital, osmosdr
        except ImportError:
            logger.exception("Failed to import GNURadio modules at runtime.")
            return None

        tb = gr.top_block()

        source = blocks.vector_source_f(signal.tolist(), repeat=False)

        if modulation.upper() == "GFSK":
            mod_block = digital.gfsk_mod()
        elif modulation.upper() == "QPSK":
            mod_block = digital.qpsk_mod()
        else:
            mod_block = blocks.multiply_const_ff(1.0)  # passthrough fallback

        sink = osmosdr.sink(args="numchan=1 driver=hackrf")
        sink.set_sample_rate(self.sample_rate)
        sink.set_center_freq(center_freq)
        sink.set_gain(gain)
        sink.set_freq_corr(0)

        tb.connect(source, mod_block, sink)
        logger.debug("Flowgraph assembled successfully.")
        return tb

    def generate_stealth_signal(
        self,
        base_signal: np.ndarray,
        target_entropy: float = 0.85,
        modulation: str = "GFSK",
        center_freq: float = 2.437e9
    ) -> Optional[object]:
        """
        Main entry for generating and optionally emitting stealth RF.
        """
        original_entropy = self.measure_entropy(base_signal)
        mutated_signal = self.apply_entropy_shift(base_signal, level=target_entropy)
        jittered_signal = self.inject_jitter(mutated_signal)
        mutated_entropy = self.measure_entropy(jittered_signal)

        logger.info(f"Entropy: {original_entropy:.3f} → {mutated_entropy:.3f}")
        logger.info(f"Signal fingerprint: {self.fingerprint_signal(jittered_signal)}")

        return self.forge_modulated_flowgraph(
            signal=jittered_signal,
            modulation=modulation,
            center_freq=center_freq
        )
