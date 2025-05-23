"""
Central registry of adversarial vectors used by the Observer Engine.
Provides metadata, requirements, simulation safety, platform constraints,
MITRE ATT&CK mappings, and capability classification.
"""

from typing import Dict, List

# Each vector maps to its dynamic function name (as loaded by attack_loader.py)
# Key = CLI/Vector ID, Value = metadata dict (handler, description, etc.)
VECTOR_REGISTRY: Dict[str, Dict] = {
    # Example attack entry
    "rf_blend": {
        "handler": "rf_blend_attack",  # <== Dynamic function name used by attack_loader.py
        "description": "Emit multi-protocol RF burst (BLE, WiFi, Zigbee) via SDR blending.",
        "tags": ["rf", "disruption", "physical"],
        "requires": ["rf_device"],
        "simulation_safe": False,
        "requires_root": True,
        "requires_linux": True,
        "mitre_tactics": ["TA0040"],
        "mitre_techniques": ["T1468"]
    },

    "siem_fracture": {
        "handler": "build_siem_perception_fracture",
        "description": "Poison SIEM models with synthetic adversarial log injections.",
        "tags": ["siem", "deception", "perception"],
        "requires": ["siem_ip"],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0005", "TA0010"],
        "mitre_techniques": ["T1001.003", "T1565.002"]
    },

    "mind_poison": {
        "handler": "deploy_dashboard_poisoning",
        "description": "Poison dashboards with fake metrics to mislead SOC operators.",
        "tags": ["cognitive", "grafana", "dashboard"],
        "requires": ["grafana_url", "grafana_token", "prometheus_url", "alert_sink_url"],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0040"],
        "mitre_techniques": ["T1036.008"]
    },

    "ritual_loop": {
        "handler": "invoke_recursive_ritual_loop",
        "description": "Run multi-layer ritual: RF blend, SIEM fracture, mind poison, DNS echo, etc.",
        "tags": ["multi", "composite", "ritual"],
        "requires": ["grafana_url", "grafana_token", "siem_ip", "dns_target"],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0005", "TA0040"],
        "mitre_techniques": ["T1565", "T1001"]
    },

    "dns_echo": {
        "handler": "deploy_dns_feedback_loop",
        "description": "Emit recursive DNS echo traffic to generate noise/beacons.",
        "tags": ["net", "dns", "deception"],
        "requires": ["dns_target"],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0011"],
        "mitre_techniques": ["T1071.004"]
    },

    "synth_lore": {
        "handler": "inject_synthetic_lore",
        "description": "Generate synthetic alert chains for deception or drill simulation.",
        "tags": ["lore", "incident", "log"],
        "requires": [],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0005"],
        "mitre_techniques": ["T1565.002"]
    },

    "gps_spoof": {
        "handler": "gps_spoof_attack",
        "description": "Inject GNSS constellation signals to spoof receiver coordinates.",
        "tags": ["rf", "gps", "position", "disruption"],
        "requires": ["rf_device", "spoof_mode"],
        "simulation_safe": False,
        "requires_root": True,
        "requires_linux": True,
        "mitre_tactics": ["TA0040"],
        "mitre_techniques": ["T1608.002"]
    },

    "ble_disrupt": {
        "handler": "ble_beacon_hijack",
        "description": "Emit rogue BLE beacons to spoof mobile dashboards and devices.",
        "tags": ["rf", "ble", "spoof", "deception"],
        "requires": ["ble_interface", "beacon_type"],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": True,
        "mitre_tactics": ["TA0040"],
        "mitre_techniques": ["T1557.001"]
    },

    "llm_poison": {
        "handler": "inject_llm_poison_logs",
        "description": "Inject prompt injection payloads into log streams to hijack LLM-based triage bots.",
        "tags": ["llm", "prompt", "poison", "siem"],
        "requires": ["splunk_url", "splunk_token"],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0005", "TA0011"],
        "mitre_techniques": ["T1565.002"]
    },

    "oauth_clone": {
        "handler": "oauth_token_clone_attack",
        "description": "Clone and reuse bearer tokens captured via passive MITM JS header analysis.",
        "tags": ["auth", "token", "identity", "replay"],
        "requires": ["grafana_url", "grafana_token"],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0006"],
        "mitre_techniques": ["T1528"]
    },

    "gsm_jammer": {
        "handler": "gsm_control_jammer",
        "description": "Jam GSM control channels via ARFCN bursts using SDR (paging denial).",
        "tags": ["rf", "gsm", "jamming", "denial"],
        "requires": ["rf_device", "jam_mode"],
        "simulation_safe": False,
        "requires_root": True,
        "requires_linux": True,
        "mitre_tactics": ["TA0040"],
        "mitre_techniques": ["T1496"]
    },

    "bgp_pollute": {
        "handler": "simulate_bgp_pollution",
        "description": "Simulate BGP prefix hijacks in telemetry logs to cause false routing alarms.",
        "tags": ["net", "bgp", "exfil", "deception"],
        "requires": [],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0010"],
        "mitre_techniques": ["T1583.006"]
    },

    "cloudtrail_ghost": {
        "handler": "inject_cloudtrail_ghosts",
        "description": "Inject CloudTrail logs for fake Lambda invocations and phantom alerts.",
        "tags": ["cloud", "aws", "log", "ghost"],
        "requires": [],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0005"],
        "mitre_techniques": ["T1565.002"]
    },

    "telemetry_invert": {
        "handler": "telemetry_inversion_attack",
        "description": "Poison Prometheus/Grafana metrics to invert real-world telemetry status.",
        "tags": ["deception", "telemetry", "c2_evasion"],
        "requires": ["prometheus_url"],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0005"],
        "mitre_techniques": ["T1036.003"]
    },

    "rfid_spoof": {
        "handler": "rfid_reflect_spoof",
        "description": "Reflect or replay RFID/HID/iCLASS badges with bit variation spoofing.",
        "tags": ["rfid", "physical", "spoof", "proxmark"],
        "requires": [],
        "simulation_safe": True,
        "requires_root": False,
        "requires_linux": False,
        "mitre_tactics": ["TA0006"],
        "mitre_techniques": ["T1078"]
    }
}


# ───────────────────────────────
# API Functions
# ───────────────────────────────

def list_all_vectors() -> List[str]:
    return list(VECTOR_REGISTRY.keys())

def get_vector_metadata(vector_id: str) -> Dict:
    return VECTOR_REGISTRY.get(vector_id, {})

def validate_vector_chain(chain: List[str]) -> bool:
    return all(v in VECTOR_REGISTRY for v in chain)

def requires_arguments(vector_id: str) -> List[str]:
    return VECTOR_REGISTRY.get(vector_id, {}).get("requires", [])

def is_simulation_safe(vector_id: str) -> bool:
    return VECTOR_REGISTRY.get(vector_id, {}).get("simulation_safe", False)

def requires_root(vector_id: str) -> bool:
    return VECTOR_REGISTRY.get(vector_id, {}).get("requires_root", False)

def requires_linux(vector_id: str) -> bool:
    return VECTOR_REGISTRY.get(vector_id, {}).get("requires_linux", False)

def get_handler_function_name(vector_id: str) -> str:
    return VECTOR_REGISTRY.get(vector_id, {}).get("handler", "")

def get_mitre_mapping(vector_id: str) -> Dict[str, List[str]]:
    meta = VECTOR_REGISTRY.get(vector_id, {})
    return {
        "tactics": meta.get("mitre_tactics", []),
        "techniques": meta.get("mitre_techniques", [])
    }

def print_vector_catalog():
    print("\n=== Vector Catalog ===")
    for name, meta in VECTOR_REGISTRY.items():
        print(f"\nVector: {name}")
        print(f"  Description     : {meta['description']}")
        print(f"  Handler         : {meta.get('handler')}")
        print(f"  Tags            : {', '.join(meta['tags'])}")
        print(f"  Requirements    : {meta.get('requires', [])}")
        print(f"  Simulation Safe : {meta.get('simulation_safe', False)}")
        print(f"  Root Required   : {meta.get('requires_root', False)}")
        print(f"  Linux Only      : {meta.get('requires_linux', False)}")
        print(f"  MITRE Tactics   : {meta.get('mitre_tactics', [])}")
        print(f"  MITRE Techniques: {meta.get('mitre_techniques', [])}")
    print("\n========================\n")
