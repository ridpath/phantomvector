# attacks/siem_perception_fracture.py

import logging
import time
import random
import json
import os
from datetime import datetime
from faker import Faker
from typing import Optional, Dict, List

logger = logging.getLogger("SIEMFracture")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

fake = Faker()

MITRE_TAGS = [
    "T1003", "T1027", "T1046", "T1059", "T1071", "T1105", "T1110", "T1203", "T1499", "T1566", "T1583"
]

PROCESS_MAP = {
    "auditd": "Host monitoring / syscall trace",
    "sshd": "Remote shell or key auth (lateral movement)",
    "nginx": "Exfil or C2 via HTTP",
    "logstash": "Logging corruption / chain injection",
    "dnsmasq": "Tunneled payloads (DNS)",
    "suricata": "IDS/IPS rule disruption",
    "winlogbeat": "SIEM sync poison",
    "systemd-journald": "Local telemetry spoof"
}

SIMULATED_TTP_EVENTS = [
    "User account created outside of change window",
    "Elevated shell established over non-standard port",
    "SIEM alert suppression anomaly detected",
    "Unexpected system time change during incident",
    "Multiple failed logins with anomalous headers",
    "Exfil domain resolved from honeypot node",
    "Executable drop in temp directory during beacon loop",
    "TTL mismatch observed in clustered event replay",
    "PowerShell payload obfuscated via base64 round-trip",
    "New service registered and started on monitored host"
]

def _generate_siem_event(
    target_ip: str,
    actor_id: Optional[str] = None,
    technique: Optional[str] = None,
    attack_tag: str = "deception",
    entropy: float = 0.0,
    extra_tags: Optional[List[str]] = None
) -> Dict:
    """
    Generates a fake SIEM event designed to mislead ML-based correlation engines.
    """
    actor = actor_id or fake.user_name()
    process = random.choice(list(PROCESS_MAP.keys()))
    mitre_id = technique or random.choice(MITRE_TAGS)
    severity = random.choices(["low", "medium", "high", "critical"], weights=[1, 2, 4, 2])[0]
    msg = random.choice(SIMULATED_TTP_EVENTS)

    message = f"[{mitre_id}] {msg} | Process: {process} | Actor: {actor} | IP: {target_ip}"
    tags = [attack_tag, "adversarial", mitre_id, "friction", "noise", random.choice(["false_positive", "ttl_shift", "temporal_desync"])]

    if extra_tags:
        tags.extend(extra_tags)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "source": process,
        "context": PROCESS_MAP[process],
        "actor": actor,
        "ip": target_ip,
        "severity": severity,
        "message": message,
        "tags": sorted(set(tags)),
        "entropy": round(entropy, 3)
    }


def build_siem_perception_fracture(
    target_ip: str,
    count: int = 12,
    delay: float = 1.0,
    entropy_score: float = 0.0,
    simulation: bool = False,
    telemetry_log: Optional[str] = None,
    output_sink: Optional[str] = None,
    tag_override: Optional[str] = None,
    correlation_cluster: Optional[str] = None
):
    """
    Military-grade SIEM attack chain to simulate adversarial behavior and fracture detection pipelines.

    Args:
        target_ip: Target sensor endpoint to spoof correlation.
        count: Number of SIEM events to simulate.
        delay: Delay between events.
        entropy_score: Adaptive signal shaping control.
        simulation: If True, no live injection occurs.
        telemetry_log: Path to write event JSONL.
        output_sink: Future REST endpoint for real SIEM injection.
        tag_override: Optional tag label for this ritual vector.
        correlation_cluster: Optional campaign chain ID.
    """
    logger.info(f"[SIEM Fracture] Starting against target {target_ip} | Count={count} | Simulation={simulation}")

    os.makedirs(os.path.dirname(telemetry_log), exist_ok=True) if telemetry_log else None

    for i in range(count):
        entry = _generate_siem_event(
            target_ip=target_ip,
            attack_tag=tag_override or "perception_fracture",
            entropy=entropy_score,
            extra_tags=[f"cluster:{correlation_cluster}"] if correlation_cluster else None
        )

        if simulation:
            logger.info(f"[SIM] {entry['timestamp']} | {entry['message']} :: {entry['severity']}")
        else:
            logger.info(f"[LIVE] Injected Event [{i+1}/{count}]: {entry['message']}")

        if telemetry_log:
            with open(telemetry_log, "a") as f:
                f.write(json.dumps(entry) + "\n")

        # Placeholder: future support for POST injection
        # if output_sink:
        #     try:
        #         requests.post(output_sink, json=entry, timeout=3)
        #     except Exception as e:
        #         logger.warning(f"[Sink] Post failed: {e}")

        time.sleep(delay)

    logger.info("[SIEM Fracture] Injection chain complete.")
