import logging
import time
import numpy as np
import random
import os
from datetime import datetime
from typing import List

try:
    from gnuradio import gr, analog, blocks, osmosdr, digital
    GNU_RADIO_AVAILABLE = True
except ImportError:
    GNU_RADIO_AVAILABLE = False

logger = logging.getLogger("RFBlend")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class RFSignalProfile:
    """
    Defines an RF profile for blending.
    """
    def __init__(self, name, freq, bandwidth, modulation, amplitude, entropy=0.0):
        self.name = name
        self.freq = freq
        self.bandwidth = bandwidth
        self.modulation = modulation.upper()
        self.amplitude = amplitude
        self.entropy = entropy

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return (f"{self.name.upper()} | {self.freq/1e6:.2f} MHz | "
                f"{self.modulation} | {self.bandwidth/1e6:.2f} MHz | Entropy={self.entropy:.2f}")


class RFBlendFlowgraph(gr.top_block):
    """
    GNU Radio flowgraph to emit a composite RF signature.
    """
    def __init__(self, profiles: List[RFSignalProfile], device="hackrf", sample_rate=2e6):
        super().__init__()
        self.sample_rate = sample_rate
        self.composite = blocks.add_cc()
        self.sources = []

        for i, profile in enumerate(profiles[:2]):  # Limit to 2 channels max
            src = self._generate_signal(profile)
            self.sources.append(src)
            self.connect(src, (self.composite, i))

        sink = osmosdr.sink(args=f"driver={device}")
        sink.set_sample_rate(sample_rate)
        sink.set_center_freq(sum(p.freq for p in profiles[:2]) / 2)
        sink.set_gain(20)
        sink.set_freq_corr(0)
        self.connect(self.composite, sink)

    def _generate_signal(self, profile):
        if profile.modulation == "AM":
            carrier = analog.sig_source_c(self.sample_rate, analog.GR_COS_WAVE, 1e3, profile.amplitude)
            noise = analog.noise_source_c(analog.GR_GAUSSIAN, profile.amplitude / 2)
            return blocks.multiply_cc(carrier, noise)

        elif profile.modulation == "FM":
            tone = analog.sig_source_f(self.sample_rate, analog.GR_SIN_WAVE, 1e3, profile.amplitude)
            modulator = analog.frequency_modulator_fc(2 * np.pi * profile.bandwidth / self.sample_rate)
            return blocks.multiply_fc(tone, modulator)

        elif profile.modulation == "GFSK":
            return digital.gfsk_mod()

        elif profile.modulation == "QPSK":
            return digital.qpsk_mod()

        else:
            return analog.noise_source_c(analog.GR_GAUSSIAN, profile.amplitude)


def simulate_rf_blending(profiles: List[RFSignalProfile], duration=5.0, simulation=True, device="hackrf"):
    """
    Simulate or emit composite RF signal.
    """
    logger.info("[RF Blend] Preparing composite emission...")
    for p in profiles:
        logger.info(f" ↳ {p}")

    if simulation or not GNU_RADIO_AVAILABLE:
        logger.info("[RF Blend] Simulation mode active.")
        time.sleep(duration)
        logger.info("[RF Blend] Simulated RF transmission complete.")
        return

    try:
        fg = RFBlendFlowgraph(profiles, device=device)
        fg.start()
        logger.info("[RF Blend] On-air transmission started...")
        time.sleep(duration)
        fg.stop()
        fg.wait()
        logger.info("[RF Blend] Transmission complete.")
    except Exception as ex:
        logger.error(f"[RF Blend] Flowgraph execution failed: {ex}")


def rf_blend_attack(
    device="hackrf",
    simulation=True,
    duration=6.0,
    entropy_score=None,
    telemetry_log=None
):
    """
    Execute an RF blend with entropy-driven parameters.
    """
    entropy_score = entropy_score or random.uniform(0.1, 0.6)
    amp_variation = 0.1 + random.random() * entropy_score

    profiles = [
        RFSignalProfile("WiFi", 2.437e9, 20e6, "FM", 0.5 + amp_variation, entropy=entropy_score),
        RFSignalProfile("BLE", 2.402e9, 2e6, "AM", 0.3 + amp_variation / 2, entropy=entropy_score)
    ]

    simulate_rf_blending(profiles, duration=duration, simulation=simulation, device=device)

    if telemetry_log:
        os.makedirs(os.path.dirname(telemetry_log), exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "device": device,
            "simulation": simulation,
            "entropy_score": entropy_score,
            "profiles": [p.to_dict() for p in profiles]
        }
        with open(telemetry_log, "a") as f:
            f.write(json.dumps(entry) + "\n")


# === Compatibility alias ===
hybrid_rf_burst = rf_blend_attack
