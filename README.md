# phantomvector ![Alpha Release](https://img.shields.io/badge/status-alpha-red)

**phantomvector** is a modular adversary simulation toolkit for cognitive, RF layer, and telemetry level deception testing. It enables red teams, researchers, and operators to simulate layered attack chains against modern blue team defenses using entropy feedback, synthetic logs, RF emissions, LLM prompt poisoning, and more.

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

## Legal & Ethical Usage Notice
This project is intended strictly for educational, research, and authorized red team use only.

Do not deploy or execute this software in any network, system, or environment without explicit written permission from the appropriate stakeholders.

Misuse of this tool including unauthorized signal emissions, infrastructure disruption, or deceptive telemetry injection may be illegal and is strictly discouraged by the authors.

The authors accept no liability for misuse or damage caused by this tool. You are solely responsible for complying with local laws and organizational security policies.

## License
MIT License 

