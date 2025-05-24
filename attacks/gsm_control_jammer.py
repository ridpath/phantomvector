import subprocess
import os
import json
import time
import random
import logging
from datetime import datetime
from typing import Optional, List

logger = logging.getLogger("GSMControlJammer")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

SUPPORTED_DEVICES = ["hackrf", "usrp", "limesdr", "bladerf"]
SUPPORTED_MODES = ["selective", "flood", "hybrid", "rach_fuzz", "sch_desync", "arfcn_hop", "burst_inject"]

DEFAULT_JAM_DURATION = 30
DEFAULT_BURST_INJECT_SCRIPT = "scripts/burst_inject.grc"


def kalibrate_scan(device: str = "hackrf") -> List[int]:
    cmd_map = {
        "hackrf": "kal -s 42",
        "bladerf": "kal -s 42 -d bladeRF",
        "rtl-sdr": "kal -s 42 -d rtl=0"
    }
    kal_cmd = cmd_map.get(device)
    if not kal_cmd:
        logger.error(f"[Kalibrate] Unsupported device: {device}")
        return []

    logger.info(f"[Kalibrate] Scanning ARFCNs...")
    try:
        out = subprocess.check_output(kal_cmd.split(), stderr=subprocess.DEVNULL).decode()
        return sorted({int(l.split()[0]) for l in out.splitlines() if "ARFCN" in l and l.strip()[0].isdigit()})
    except Exception as e:
        logger.error(f"[Kalibrate] Failed: {e}")
        return []


def calculate_arfcn_freq(arfcn: int) -> float:
    return 935.0 + (arfcn * 0.2)


def build_grgsm_trx_cmd(device: str, arfcn: int) -> str:
    freq = calculate_arfcn_freq(arfcn)
    args = "--args 'uhd'" if device == "usrp" else f"--args 'driver={device}'"
    return f"grgsm_trx -a {freq}e6 -b {arfcn} {args} --gain 47"


def simulate_imsi_paging_hook(arfcn: int):
    fake_imsi = f"00101{random.randint(100000000,999999999)}"
    logger.info(f"[IMSI Paging] Sending decoy IMSI {fake_imsi} on ARFCN {arfcn}")
    return fake_imsi


def execute_jamming_flow(arfcn: int, device: str, duration: int):
    cmd = build_grgsm_trx_cmd(device, arfcn)
    try:
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(duration)
        proc.terminate()
        logger.info(f"[Selective Jam] ARFCN {arfcn} complete.")
    except Exception as e:
        logger.error(f"[Selective Jam] Failed: {e}")


def fuzz_rach(device: str, duration: int):
    logger.info("[RACH] Fuzzing RACH bursts...")
    for _ in range(duration):
        logger.info("[Fuzz] Transmitting malformed RACH signal")
        time.sleep(1.3)


def sch_desync(arfcn: int, device: str, duration: int):
    logger.info("[SCH] Executing synchronization desync on ARFCN %d", arfcn)
    for _ in range(duration):
        logger.info("[Desync] Sending misaligned SCH burst")
        time.sleep(1.2)


def arfcn_hop_burst(arfcn_list: List[int], device: str, duration: int):
    logger.info("[Hop Mode] Confusion burst with rapid ARFCN rotation")
    end_time = time.time() + duration
    while time.time() < end_time:
        target = random.choice(arfcn_list)
        freq = calculate_arfcn_freq(target)
        logger.info(f"[Hop] Injected confusion burst on ARFCN {target} @ {freq:.2f} MHz")
        time.sleep(0.9)


def burst_injection_attack(arfcn: int, device: str, grc_file: str = DEFAULT_BURST_INJECT_SCRIPT, duration: int = 10):
    logger.info(f"[Burst Inject] Starting GRC-based burst injection on ARFCN {arfcn}")
    freq = calculate_arfcn_freq(arfcn)
    try:
        grc_cmd = f"gnuradio-companion -t {grc_file} -a {freq}e6 --device {device}"
        proc = subprocess.Popen(grc_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(duration)
        proc.terminate()
        logger.info("[Burst Inject] Completed injection routine.")
    except Exception as e:
        logger.error(f"[Burst Inject] Failed to execute: {e}")


def gsm_control_jammer(
    device: str = "hackrf",
    duration: int = DEFAULT_JAM_DURATION,
    mode: str = "selective",
    max_targets: int = 3,
    simulation: bool = True,
    telemetry_log: Optional[str] = None
):
    if device not in SUPPORTED_DEVICES:
        logger.error(f"[GSM] Invalid SDR device: {device}")
        return

    if mode not in SUPPORTED_MODES:
        logger.error(f"[GSM] Invalid jamming mode: {mode}")
        return

    targets = kalibrate_scan(device)
    if not targets:
        logger.warning("[GSM] No ARFCNs detected.")
        return

    selected = (
        random.sample(targets, min(len(targets), max_targets))
        if mode != "flood"
        else targets
    )

    for arfcn in selected:
        freq = calculate_arfcn_freq(arfcn)
        logger.info(f"[Target] ARFCN {arfcn} ({freq:.2f} MHz) Mode: {mode}")

        if telemetry_log:
            os.makedirs(os.path.dirname(telemetry_log), exist_ok=True)
            with open(telemetry_log, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "arfcn": arfcn,
                    "frequency_mhz": freq,
                    "device": device,
                    "mode": mode,
                    "simulation": simulation
                }) + "\n")

        if simulation:
            simulate_imsi_paging_hook(arfcn)
            time.sleep(1.5)
            continue

        if mode == "selective":
            execute_jamming_flow(arfcn, device, duration)
        elif mode == "rach_fuzz":
            fuzz_rach(device, duration)
        elif mode == "sch_desync":
            sch_desync(arfcn, device, duration)
        elif mode == "arfcn_hop":
            arfcn_hop_burst(targets, device, duration)
        elif mode == "burst_inject":
            burst_injection_attack(arfcn, device, DEFAULT_BURST_INJECT_SCRIPT, duration)
        else:
            logger.warning(f"[Mode] Unknown: {mode}")
            continue

    logger.info("[GSMJammer] Mission complete.")
