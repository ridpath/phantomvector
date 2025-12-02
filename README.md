<!--
phantomvector, RF adversary simulator, GNSS spoofing toolkit, SDR offensive security,
SIEM deception research tool, synthetic telemetry poisoning, Grafana adversarial testing,
BLE beacon hijacking, OT/ICS RF attack simulation, DNS covert channel generation,
LLM SOC deception, prompt poisoning SIEM logs, cognitive attack vector simulation,
entropy-based red team automation, multi-layer deception framework, cybersecurity AI testing,
RF telemetry fuzzing with SDR, stealth signal testing kernel-level,
GNURadio offensive testing tools, PyRF exploitation lab,
advanced threat emulation toolkit, hybrid RF + AI adversarial ops,
research and authorized lab-only usage
-->

# phantomvector
![status: alpha](https://img.shields.io/badge/status-alpha-red)
![license: MIT](https://img.shields.io/badge/license-MIT-blue)
![platform: Linux-first](https://img.shields.io/badge/platform-Linux%20First-black)
![rf-capable](https://img.shields.io/badge/RF%20Enabled-SDR%20Required-purple)
![domain: deception](https://img.shields.io/badge/domain-adversarial%20deception-darkgreen)


**phantomvector** is a modular adversary simulation toolkit for cognitive, RF layer, and telemetry level deception testing. It enables red teams, researchers, and operators to simulate layered attack chains against modern blue team defenses using entropy feedback, synthetic logs, RF emissions, LLM prompt poisoning, and more.

> `phantomvector` is in **alpha** — use at your own risk. Expect bugs, instability, and rapid changes.  

---

## Features

- Recursive ritual chaining and attack composition
- Entropy aware feedback loop engine
- Adversarial telemetry poisoning (Grafana, Prometheus, Splunk, SIEM)
- GNSS spoofing with SDR
- BLE beacon hijack and RF blends (WiFi/BLE/Zigbee)
- DNS echo exfiltration + signal noise generation
- Prompt injection logs for LLM-based SOC systems
- Operator mind deception (dashboard misdirection)
- Full YAML ritual chain support
- Modular vector registry with MITRE ATT&CK mapping

## MITRE ATT&CK Technique Mapping

| Category | Technique | ID |
|---------|-----------|----|
| Command & Control | Covert Channels | T1573 |
| Defense Evasion | Indicator Removal on Host | T1070 |
| Defense Evasion | Software Packing / Obfuscation | T1027 |
| Collection | Exfiltration Over Alternative Protocol | T1048 |
| Discovery | Network Service Scanning | T1046 |
| Impact | System Firmware Manipulation (GNSS spoofing context) | T1542.004 |
| Initial Access (SOC bypass) | Valid Accounts / Telemetry Manipulation | T1078/T1565 |
| Adversary Disruption | Data Manipulation (SIEM/Splunk/Grafana) | T1565 |
| Lateral Movement | Wireless Compromise (BLE/WiFi/Zigbee) | T1599.001 |


---

## Requirements

- Python 3.10+
- GNU Radio (optional, for RF vectors)
- Linux (recommended for full RF capability)
- Python packages (see `requirements.txt`)
- SDR hardware (e.g., HackRF, bladeRF) for real emissions

---

## Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/YOUR_USERNAME/phantomvector.git
cd phantomvector
pip install -r requirements.txt
```
Usage
Run the interactive shell:

```bash
python3 engine.py --shell
```

Or execute a single attack vector:
```bash
python3 engine.py --vector siem_fracture --siem_ip 192.168.1.10 --simulation
```

Run a full ritual chain from YAML:
```bash
python3 engine.py --chain ops/ritual_chains.yaml
```

All CLI flags are documented via:
```bash
python3 engine.py --help
```

## Contributing
All contributions are welcome. To add a new attack:

Create a new .py module in attacks/.

Register the vector in core/vector_registry.py.

Optionally integrate it into core/attack_loader.py or engine.py.

Test via --shell or chain config.

Open a PR with description and test output.

### Legal & Ethical Usage Notice

phantomvector exists **only** for:

- Academic research
- Red team simulations with **written authorization**
- Security validation of **controlled testbeds**
- SIEM + RF deception analysis in **lab environments**

Improper or unauthorized usage can:

- Interfere with licensed RF spectrum
- Disrupt safety critical infrastructure
- Violate regional and international laws

Users must ensure **full compliance** with:

- RF emission laws (FCC / ETSI)
- Local computer misuse regulations
- Corporate / network scope agreements

The authors assume **zero liability** for misuse.


## License
MIT License 

<!--
Keywords: phantomvector adversary simulator,
RF deception toolkit, GNSS spoofing red team lab,
SIEM poisoning automation, telemetry deception researchers,
SDR hacking utilities, Grafana log tampering,
LLM SOC evasion testing, entropy-driven attack chaining,
signal operations cybersecurity, OT wireless attack simulation,
protocol noise injection tools, red team operational stealth,
authorized penetration testing utilities, cybersecurity deception framework,
attack chain orchestrations, SDR-based signal injection testing
-->
