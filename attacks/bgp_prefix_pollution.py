import logging
import random
import json
import os
import time
from datetime import datetime
from faker import Faker
from typing import Optional, List

logger = logging.getLogger("BGPPrefixPollution")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

fake = Faker()

RIRs = ["ARIN", "RIPE", "APNIC", "LACNIC", "AFRINIC"]

BGP_EVENT_TYPES = [
    "announcement",
    "withdrawal",
    "route-flap",
    "route-leak"
]

def _generate_fake_bgp_event() -> dict:
    """
    Craft a fake BGP event mimicking route manipulation or hijack conditions.
    """
    prefix = f"{random.randint(1, 223)}.{random.randint(0,255)}.{random.randint(0,255)}.0/{random.choice([24, 23, 22, 16])}"
    origin_asn = random.randint(64512, 65535)  # Private ASN for simulation
    seen_asn_path = [origin_asn] + random.sample(range(64512, 65500), k=random.randint(1, 4))
    rir = random.choice(RIRs)
    mismatch_flag = random.random() < 0.4  # 40% chance of RIR mismatch
    polluted_by = fake.asn()
    now = datetime.utcnow().isoformat() + "Z"

    return {
        "timestamp": now,
        "type": random.choice(BGP_EVENT_TYPES),
        "prefix": prefix,
        "origin_asn": origin_asn,
        "seen_path": seen_asn_path,
        "rir_expected": rir,
        "rir_actual": random.choice([r for r in RIRs if r != rir]) if mismatch_flag else rir,
        "mismatch": mismatch_flag,
        "polluted_by": polluted_by,
        "confidence": round(random.uniform(0.4, 0.98), 2)
    }


def generate_bgp_event_batch(count: int = 10) -> List[dict]:
    return [_generate_fake_bgp_event() for _ in range(count)]


def write_bgp_logfile(path: str = "data/fake_bgp_pollution.json", count: int = 12):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    logs = generate_bgp_event_batch(count)
    with open(path, "w") as f:
        json.dump({"bgp_alerts": logs}, f, indent=2)
    logger.info(f"[BGP Pollution] Written {count} synthetic events to {path}")


def inject_to_splunk(logs: List[dict], splunk_url: str, token: str):
    import requests
    headers = {
        "Authorization": f"Splunk {token}",
        "Content-Type": "application/json"
    }
    for event in logs:
        payload = {
            "event": event,
            "sourcetype": "bgp:alert",
            "time": time.time()
        }
        try:
            res = requests.post(splunk_url, headers=headers, data=json.dumps(payload), timeout=3)
            logger.info(f"[Splunk] Injected BGP event: {res.status_code}")
        except Exception as e:
            logger.warning(f"[Splunk] Injection failed: {e}")


def simulate_bgp_pollution(
    count: int = 10,
    output_path: Optional[str] = "data/fake_bgp_pollution.json",
    splunk_url: Optional[str] = None,
    splunk_token: Optional[str] = None,
    simulation: bool = False,
    telemetry_log: Optional[str] = None
):
    """
    Perform a full BGP pollution attack simulation.
    """
    logs = generate_bgp_event_batch(count)

    if simulation:
        for event in logs:
            logger.info(f"[SIM] Prefix: {event['prefix']} | Mismatch: {event['mismatch']} | Origin ASN: {event['origin_asn']}")
    else:
        if output_path:
            write_bgp_logfile(path=output_path, count=count)

        if splunk_url and splunk_token:
            inject_to_splunk(logs, splunk_url, splunk_token)

    if telemetry_log:
        os.makedirs(os.path.dirname(telemetry_log), exist_ok=True)
        with open(telemetry_log, "a") as f:
            for event in logs:
                f.write(json.dumps(event) + "\n")
