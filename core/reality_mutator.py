import random
import time
import logging
import subprocess
from typing import Optional, Union
from scapy.all import IP, TCP, UDP, Raw, Ether, Packet

logger = logging.getLogger("RealityMutator")
logger.setLevel(logging.DEBUG)

# =============================
# ─── STATIC FAKE PROFILES ───
# =============================

FAKE_MAC_PREFIXES = [
    "00:11:22", "AA:BB:CC", "DE:AD:BE", "FA:KE:12", "CA:FE:FE"
]

OS_FINGERPRINTS = [
    {"ttl": 64, "window": 5840, "df": 1, "os": "Linux 2.6"},
    {"ttl": 128, "window": 8192, "df": 1, "os": "Windows XP"},
    {"ttl": 255, "window": 4128, "df": 0, "os": "Cisco Router"},
    {"ttl": 32, "window": 14600, "df": 1, "os": "FreeBSD"},
    {"ttl": 100, "window": 32120, "df": 0, "os": "IoT Generic"}
]

TCP_OPTION_SETS = [
    [('MSS', 1460), ('WScale', 7), ('NOP', None), ('Timestamp', (12345, 0))],
    [('SAckOK', b''), ('NOP', None), ('Timestamp', (98765, 0)), ('MSS', 1360)]
]

# =============================
# ─── PROTOCOL MUTATIONS ─────
# =============================

def inject_protocol_drift(pkt: Union[Packet, bytes]) -> Packet:
    """
    Apply a random protocol drift mutation.

    Args:
        pkt: Raw bytes or Scapy Packet

    Returns:
        Mutated packet (Scapy)
    """
    if isinstance(pkt, bytes):
        pkt = Raw(load=pkt)

    mutation_type = random.choice(["ttl", "tcpopts", "timestamps", "padding"])
    logger.debug(f"[Mutator] Applying mutation: {mutation_type}")

    try:
        if mutation_type == "ttl":
            return _mutate_ttl(pkt)
        elif mutation_type == "tcpopts":
            return _mutate_tcp_options(pkt)
        elif mutation_type == "timestamps":
            return _mutate_timestamps(pkt)
        elif mutation_type == "padding":
            return _mutate_padding(pkt)
    except Exception as e:
        logger.warning(f"[Mutator] Failed to apply {mutation_type}: {e}")
    return pkt


def inject_protocol_anomalies(proto: str = "http", level: str = "moderate"):
    """
    Simulate higher-layer anomalies in app protocol behavior.

    Args:
        proto: Protocol name
        level: Mutation level/intensity
    """
    logger.info(f"[AnomalyInjector] Injecting {level.upper()} anomalies into {proto.upper()} stream")
    # Placeholder – actual protocol stack manipulation would go here

# =============================
# ─── PACKET MUTATIONS ─────
# =============================

def _mutate_ttl(pkt: Packet) -> Packet:
    if IP in pkt:
        fp = random.choice(OS_FINGERPRINTS)
        pkt[IP].ttl = fp["ttl"]
        pkt[IP].flags = 'DF' if fp["df"] else 0
        if TCP in pkt:
            pkt[TCP].window = fp["window"]
    return pkt


def _mutate_tcp_options(pkt: Packet) -> Packet:
    if TCP in pkt:
        opts = random.choice(TCP_OPTION_SETS)
        random.shuffle(opts)
        pkt[TCP].options = opts
    return pkt


def _mutate_timestamps(pkt: Packet) -> Packet:
    try:
        jitter = random.randint(-5000, 5000)
        pkt.time += jitter / 1000.0
    except Exception:
        pass
    return pkt


def _mutate_padding(pkt: Packet) -> Packet:
    if Raw in pkt:
        pad_len = random.randint(8, 32)
        pkt[Raw].load += bytes(random.randint(0, 255) for _ in range(pad_len))
    return pkt

# =============================
# ─── FULL LAYER CHAIN ─────
# =============================

def warp_reality_on_wire(pkt: Packet) -> Packet:
    """
    Apply all known mutation techniques.

    Args:
        pkt: Input packet

    Returns:
        Fully mutated output
    """
    logger.debug("[Mutator] Full-stack reality distortion initiated")
    pkt = _mutate_ttl(pkt)
    pkt = _mutate_tcp_options(pkt)
    pkt = _mutate_timestamps(pkt)
    pkt = _mutate_padding(pkt)
    return pkt

# =============================
# ─── NETWORK SURFACE SPOOF ─────
# =============================

def spoof_mac() -> str:
    prefix = random.choice(FAKE_MAC_PREFIXES)
    suffix = ":".join(f"{random.randint(0, 255):02x}" for _ in range(3))
    return f"{prefix}:{suffix}"


def spoof_os_fingerprint() -> dict:
    return random.choice(OS_FINGERPRINTS)


def spoof_network_surface(interface: str = "eth0") -> Optional[str]:
    new_mac = spoof_mac()
    try:
        subprocess.run(["ifconfig", interface, "down"], check=True)
        subprocess.run(["ifconfig", interface, "hw", "ether", new_mac], check=True)
        subprocess.run(["ifconfig", interface, "up"], check=True)
        logger.info(f"[Spoof] MAC address spoofed to {new_mac} on interface {interface}")
        return new_mac
    except Exception as e:
        logger.error(f"[Spoof] Failed to spoof MAC: {e}")
        return None

# =============================
# ─── RFID UID MUTATION ─────
# =============================

def generate_entropy_uid_mutation(uid: str, entropy_level: float = 0.5) -> str:
    """
    Apply entropy-based bitwise mutation to an RFID UID.

    Args:
        uid: UID string (e.g. "04AABBCCDD")
        entropy_level: Float 0.0–1.0 (mutation intensity)

    Returns:
        Mutated UID hex string
    """
    import binascii

    try:
        uid_bytes = bytearray.fromhex(uid)
        mutations = max(1, int(len(uid_bytes) * entropy_level))

        for _ in range(mutations):
            index = random.randint(0, len(uid_bytes) - 1)
            uid_bytes[index] ^= random.randint(1, 255)

        return binascii.hexlify(uid_bytes).decode().upper()
    except Exception as e:
        logger.error(f"[RFID] UID mutation failed: {e}")
        return uid
