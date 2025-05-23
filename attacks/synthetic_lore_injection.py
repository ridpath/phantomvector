import json
import random
import time
import os
import logging
from datetime import datetime, timedelta
from faker import Faker
from typing import List, Optional

# Setup
fake = Faker()
logger = logging.getLogger("SyntheticLore")
logger.setLevel(logging.DEBUG)

# === Constants ===

THREAT_ACTORS = ["APT29", "FIN7", "UNC2452", "Sandworm", "DarkHydrus", "Cobalt Spider"]
MITRE_TECHNIQUES = ["T1059", "T1086", "T1203", "T1071", "T1566", "T1547", "T1021"]
TARGET_SYSTEMS = ["mail-gateway", "erp-core", "vpn-node-7", "dmz-rtr", "admin-pc-1", "db-replica-4"]
PROCESSES = ["sshd", "nginx", "python3", "systemd", "cron", "winlogbeat", "kubelet"]

# === Core Event Generator ===

def generate_fake_log_entry(
    threat_actor: Optional[str] = None,
    mitre_id: Optional[str] = None,
    base_time: Optional[datetime] = None,
    delta_range: int = 240,
    entropy: float = 0.0
) -> dict:
    """
    Create a single fake log line with realistic security metadata.
    """
    timestamp = (base_time or datetime.utcnow()) + timedelta(minutes=random.randint(-delta_range, 0))
    actor = threat_actor or random.choice(THREAT_ACTORS)
    technique = mitre_id or random.choice(MITRE_TECHNIQUES)
    target = random.choice(TARGET_SYSTEMS)
    proc = random.choice(PROCESSES)

    message = random.choice([
        f"Observed suspicious behavior in {proc} targeting {target} linked to {actor}",
        f"Technique {technique} matched on node {target} (actor: {actor})",
        f"Unexpected SSH session on {target} tied to known IOCs for {actor}",
        f"Stage 2 loader activated from {target} matching MITRE {technique}",
        f"Recon activity logged by {proc} on {target}, linked to campaign {actor}"
    ])

    return {
        "timestamp": timestamp.isoformat(),
        "host": fake.hostname(),
        "ip": fake.ipv4_public(),
        "mac": fake.mac_address(),
        "process": proc,
        "actor": actor,
        "technique": technique,
        "target": target,
        "message": message,
        "entropy": round(entropy + random.uniform(0.1, 1.0), 3),
        "tags": [actor, technique, "deception", "synthetic", "ritual"]
    }

# === Main Ritual Chain Generator ===

def synth_lore_injector(
    path: str = "data/fake_incident_chain.json",
    count: int = 15,
    actor: Optional[str] = None,
    campaign_label: str = "op_mirage",
    entropy_seed: float = 0.0,
    jsonl_path: Optional[str] = None,
    simulation: bool = False
):
    """
    Fabricate a chain of logs for adversary simulation or deception campaigns.

    Args:
        path (str): Full JSON output path
        count (int): Number of entries to emit
        actor (str): Actor override
        campaign_label (str): Campaign identifier
        entropy_seed (float): Initial entropy used in log scoring
        jsonl_path (str): Optional streaming JSONL log path
        simulation (bool): Print output but skip file writes
    """
    base_time = datetime.utcnow()
    entries = []

    for _ in range(count):
        log = generate_fake_log_entry(
            threat_actor=actor,
            mitre_id=random.choice(MITRE_TECHNIQUES),
            base_time=base_time,
            entropy=entropy_seed
        )
        log["campaign"] = campaign_label
        entries.append(log)

        if simulation:
            print(f"[{log['timestamp']}] {log['message']}")

        if jsonl_path:
            try:
                os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
                with open(jsonl_path, "a") as f:
                    f.write(json.dumps(log) + "\n")
            except Exception as e:
                logger.warning(f"Could not write to JSONL file: {e}")

    # Write complete JSON chain
    if not simulation:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(entries, f, indent=2)
            logger.info(f"Synthetic lore chain written to: {path}")
        except Exception as e:
            logger.error(f"Failed to write JSON file: {e}")

    if jsonl_path and not simulation:
        logger.info(f"Appended {count} entries to JSONL: {jsonl_path}")

# Export for engine.py
__all__ = ["synth_lore_injector"]
