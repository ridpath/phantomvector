import os
import json
import time
import math
import random
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger("ObserverBrain")
logger.setLevel(logging.DEBUG)

DEFAULT_MEMORY_FILE = "data/ritual_memory.json"


class ObserverBrain:
    """
    Adaptive adversarial planning engine with memory retention,
    decay scoring, vector selection, and context-aware chaining.
    """

    def __init__(self, memory_file: str = DEFAULT_MEMORY_FILE):
        self.memory_file = memory_file
        self.ritual_memory: List[Dict] = []
        self.attack_success_rates: Dict[str, Dict[str, float]] = {}
        self.context_tags: Dict[str, List[str]] = {}
        self.ritual_chains: List[Dict] = []
        self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    self.ritual_memory = data.get("ritual_memory", [])
                    self.attack_success_rates = data.get("attack_success_rates", {})
                    self.context_tags = data.get("context_tags", {})
                    self.ritual_chains = data.get("ritual_chains", [])
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                self.ritual_memory = []
                self.attack_success_rates = {}
                self.context_tags = {}
                self.ritual_chains = []

    def _save_memory(self):
        payload = {
            "ritual_memory": self.ritual_memory,
            "attack_success_rates": self.attack_success_rates,
            "context_tags": self.context_tags,
            "ritual_chains": self.ritual_chains
        }
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, "w") as f:
            json.dump(payload, f, indent=2)

    def _decayed_score(self, success: int, total: int, age_hours: float) -> float:
        if total == 0:
            return 0.0
        decay = math.exp(-age_hours / 24.0)
        return (success / total) * decay

    def record_attack(self, attack_name: str, success: bool, tags: Optional[List[str]] = None):
        now = time.time()

        self.ritual_memory.append({
            "name": attack_name,
            "success": success,
            "timestamp": now
        })

        if attack_name not in self.attack_success_rates:
            self.attack_success_rates[attack_name] = {
                "success": 0,
                "total": 0,
                "last": now
            }

        self.attack_success_rates[attack_name]["total"] += 1
        if success:
            self.attack_success_rates[attack_name]["success"] += 1
        self.attack_success_rates[attack_name]["last"] = now

        if tags:
            current = self.context_tags.get(attack_name, [])
            self.context_tags[attack_name] = list(set(current + tags))

        self._save_memory()

    def log_ritual(self, label: str, chain: List[str], result: str, entropy_delta: Optional[float] = None):
        entry = {
            "label": label,
            "chain": chain,
            "result": result,
            "entropy_delta": entropy_delta,
            "timestamp": time.time()
        }
        self.ritual_chains.append(entry)
        self._save_memory()

    def score_attack(self, attack_name: str) -> float:
        stats = self.attack_success_rates.get(attack_name)
        if not stats:
            return 0.0
        age_hours = (time.time() - stats["last"]) / 3600.0
        return self._decayed_score(stats["success"], stats["total"], age_hours)

    def get_tagged_attacks(self, tag: str) -> List[str]:
        return [name for name, tags in self.context_tags.items() if tag in tags]

    def choose_next_attack(self, available: List[str], preferred_tag: Optional[str] = None) -> str:
        pool = available
        if preferred_tag:
            pool = [a for a in available if a in self.get_tagged_attacks(preferred_tag)] or pool

        if not pool:
            return random.choice(available)

        weighted = [(a, max(self.score_attack(a), 0.05)) for a in pool]
        options, weights = zip(*weighted)
        return random.choices(options, weights=weights, k=1)[0]

    def suggest_ritual_chain(self, available_attacks: List[str], length: int = 3) -> List[str]:
        chain = []
        seen = set()

        for _ in range(length):
            tag_hint = random.choice(["rf", "mind", "net", "siem", "lore", "noise"])
            candidates = [a for a in available_attacks if a not in seen]
            if not candidates:
                break
            chosen = self.choose_next_attack(candidates, preferred_tag=tag_hint)
            chain.append(chosen)
            seen.add(chosen)

        return chain

    def get_top_tags(self, limit: int = 5) -> Dict[str, int]:
        freq = defaultdict(int)
        for tags in self.context_tags.values():
            for tag in tags:
                freq[tag] += 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:limit])

    def get_strategy_report(self) -> Dict:
        return {
            "total_attacks": len(self.ritual_memory),
            "unique_vectors": len(self.attack_success_rates),
            "top_attacks": sorted(
                ((name, self.score_attack(name)) for name in self.attack_success_rates),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "recent_rituals": self.ritual_chains[-3:],
            "common_tags": self.get_top_tags()
        }

    def print_report(self):
        report = self.get_strategy_report()
        print("\n=== Observer Brain Report ===")
        print(f"Total Recorded Attacks : {report['total_attacks']}")
        print(f"Unique Attack Vectors  : {report['unique_vectors']}\n")

        print("Top 5 Vectors (Decay-Aware):")
        for name, score in report["top_attacks"]:
            print(f"  - {name:20} : {score:.3f}")

        print("\nRecent Ritual Chains:")
        for ritual in report["recent_rituals"]:
            ts = datetime.fromtimestamp(ritual["timestamp"]).isoformat()
            print(f"  [{ritual['label']}] {ritual['chain']} @ {ts} (Result: {ritual['result']})")

        print("\nMost Common Context Tags:")
        for tag, count in report["common_tags"].items():
            print(f"  - #{tag:<15}: {count}")
        print("=============================\n")


# ───────────────────────────────────────────────────────────
# External Heuristic Called From Recursive Ritual Chain
# ───────────────────────────────────────────────────────────

def ritual_score_vector(context: Dict) -> float:
    """
    Score based on entropy delta and previous loop scores.
    """
    deltas = context.get("signal_entropy_history", [])
    ritual_scores = context.get("ritual_scores", [])

    if not deltas:
        return 0.0

    avg_delta = sum((b - a for a, b in deltas)) / len(deltas)
    avg_score = sum(ritual_scores) / len(ritual_scores) if ritual_scores else 0.0

    composite_score = (avg_delta * 2.0) + (avg_score * 1.25)
    logger.debug(f"[Ritual Score] ΔEntropy={avg_delta:.3f}, AvgScore={avg_score:.3f}, Composite={composite_score:.3f}")
    return round(composite_score, 3)
