import os
import json
import argparse
import logging

try:
    import argcomplete
    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False

DEFAULT_CONFIG_PATH = "config.json"
logger = logging.getLogger("ConfigLoader")

def load_config(path: str = DEFAULT_CONFIG_PATH) -> dict:
    """
    Load configuration from disk.
    """
    if not os.path.exists(path):
        logger.warning(f"[Config] Missing config file: {path}")
        return {}
    try:
        with open(path, "r") as f:
            data = json.load(f)
            logger.info(f"[Config] Loaded: {path}")
            return data
    except Exception as e:
        logger.error(f"[Config] Failed to load config: {e}")
        return {}

def merge_args_with_config(args, config: dict):
    """
    Fills missing argparse args with values from config.json.
    """
    for key, val in config.items():
        if getattr(args, key, None) in [None, '', False]:
            setattr(args, key, val)
    return args

def build_parser():
    """
    Build full argument parser for the Observer Engine CLI.
    """
    parser = argparse.ArgumentParser(
        description="Observer Engine :: Adversarial Red Teaming Framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # ───────────────────────────────
    # EXECUTION MODES
    # ───────────────────────────────
    exec_group = parser.add_argument_group("Execution Modes")
    exec_group.add_argument("--ritual", action="store_true", help="Run entropy-driven auto-ritual chain")
    exec_group.add_argument("--shell", action="store_true", help="Interactive ritual CLI shell")
    exec_group.add_argument("--chain", type=str, help="Run a ritual chain from YAML definition")
    exec_group.add_argument("--list-chains", action="store_true", help="List known ritual chains")
    exec_group.add_argument("--list-vectors", action="store_true", help="List all vector IDs")
    exec_group.add_argument("--filter-tag", type=str, help="Only show vectors with given tag (e.g., rf, siem)")
    exec_group.add_argument("--filter-platform", choices=["linux", "root"], help="Filter vectors by platform dependency")

    # ───────────────────────────────
    # TARGET & INFRASTRUCTURE
    # ───────────────────────────────
    env_group = parser.add_argument_group("Target & Platform Configuration")
    env_group.add_argument("--siem-ip", type=str, help="Target SIEM IP")
    env_group.add_argument("--grafana-url", type=str, help="Grafana instance URL")
    env_group.add_argument("--grafana-token", type=str, help="Grafana bearer token")
    env_group.add_argument("--splunk-url", type=str, help="Splunk HEC endpoint")
    env_group.add_argument("--splunk-token", type=str, help="Splunk HEC token")
    env_group.add_argument("--prometheus-url", type=str, help="Prometheus push gateway")
    env_group.add_argument("--alert-sink-url", type=str, help="Alert sink (AlertManager or webhooks)")
    env_group.add_argument("--dns-target", type=str, help="Target DNS IP for echo beacon")

    # BLE
    env_group.add_argument("--ble-interface", type=str, default="hci0", help="BLE device interface (e.g. hci0)")
    env_group.add_argument("--beacon-type", type=str, default="ibeacon", choices=["ibeacon", "eddystone", "custom"], help="BLE beacon protocol")
    env_group.add_argument("--ble-duration", type=int, default=20, help="Beacon hijack duration (seconds)")

    # SDR / RF / GPS
    env_group.add_argument("--rf-device", type=str, default="hackrf", choices=["hackrf", "usrp", "limesdr", "bladerf"], help="SDR device")
    env_group.add_argument("--jam-mode", type=str, default="selective", choices=["selective", "flood", "hybrid"], help="GSM jamming strategy")
    env_group.add_argument("--spoof-mode", type=str, default="static", choices=["static", "drift", "kml", "gpx"], help="GPS spoofing style")
    env_group.add_argument("--spoof-duration", type=int, default=20, help="GPS spoof duration (seconds)")
    env_group.add_argument("--spoof-path", type=str, help="KML/GPX file for dynamic spoofing path")

    # ───────────────────────────────
    # ENGINE CONFIGURATION
    # ───────────────────────────────
    meta_group = parser.add_argument_group("Engine Behavior")
    meta_group.add_argument("--simulation", action="store_true", help="Dry run mode - no RF/emissions/log injection")
    meta_group.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH, help="Path to config file (JSON)")
    meta_group.add_argument("--telemetry-log", type=str, default="data/ritual_exec_log.jsonl", help="Where to write telemetry results")
    meta_group.add_argument("--verbosity", type=str, choices=["debug", "info", "warn", "error"], default="info", help="Log verbosity level")

    # ───────────────────────────────
    # COMPLETION
    # ───────────────────────────────
    if ARGCOMPLETE_AVAILABLE:
        argcomplete.autocomplete(parser)

    return parser
