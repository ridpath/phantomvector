import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import List

from core.observer_brain import ObserverBrain
from core.entropy_feedback_loop import EntropyFeedbackLoop
from core.signal_reforge import SignalReforger
from core.config_loader import build_parser, load_config, merge_args_with_config
from core.vector_registry import (
    VECTOR_REGISTRY, validate_vector_chain, get_vector_metadata,
    is_simulation_safe, requires_arguments, list_all_vectors,
    requires_root, requires_linux
)
from core.ritual_executor import RitualExecutor, list_available_chains
from core.attack_loader import load_all_attacks  

# Paths
TELEMETRY_LOG = "data/ritual_exec_log.jsonl"
DEBUG_LOG = "logs/observer_debug.log"
DATA_PATH = "data/resonance_vectors.json"

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(DEBUG_LOG, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("phantomvector")

# Conditional capability
try:
    from gnuradio import osmosdr
    HAS_OSMOSDR = True
except ImportError:
    HAS_OSMOSDR = False


class phantomvector:
    def __init__(self, args):
        self.args = args
        self.brain = ObserverBrain()
        self.entropy = EntropyFeedbackLoop()
        self.signal_forge = SignalReforger(simulation=args.simulation)
        self.vectors = self._load_vector_set()
        self.vector_handlers = load_all_attacks()  

        logger.info("Engine Mode: %s", "SIMULATION" if args.simulation else "LIVE")
        logger.debug("Parsed CLI/Config Args: %s", vars(args))

        if os.geteuid() != 0:
            logger.warning("Root privileges not detected. RF or privileged modules may fail.")
        logger.info("Module Capability Status: osmosdr=%s", "ENABLED" if HAS_OSMOSDR else "DISABLED")

    def _load_vector_set(self) -> List[str]:
        if not os.path.exists(DATA_PATH):
            logger.warning("Vector DB missing, loading default test vectors.")
            return ["camera_jam", "gps_spoof", "ble_disrupt"]
        with open(DATA_PATH, "r") as f:
            raw = json.load(f).get("vectors", [])
            return [v for v in raw if v in VECTOR_REGISTRY]

    def _prompt_missing_args(self, vector_id: str):
        for arg in requires_arguments(vector_id):
            if not getattr(self.args, arg, None):
                setattr(self.args, arg, input(f"[Input] Provide value for '{arg}': "))

    def _validate_platform(self, vector_id: str) -> bool:
        if requires_root(vector_id) and os.geteuid() != 0:
            logger.warning(f"[{vector_id}] Skipped - requires root.")
            return False
        if requires_linux(vector_id) and os.name != "posix":
            logger.warning(f"[{vector_id}] Skipped - requires Linux.")
            return False
        return True

    def _check_dependencies(self, vector_id: str) -> bool:
        if vector_id in ["rf_blend", "gsm_jammer"] and not HAS_OSMOSDR:
            logger.warning(f"[{vector_id}] Missing dependency: gnuradio/osmosdr.")
            return False
        return True

    def run_single_ritual(self):
        ritual = self.brain.suggest_ritual_chain(self.vectors)
        if not validate_vector_chain(ritual):
            logger.error(f"Invalid chain: {ritual}")
            return
        logger.info(f"Running Ritual Chain: {ritual}")
        entropy_score = self.entropy.state.current_score
        results = [(v, self.execute_vector(v)) for v in ritual]
        self.brain.log_ritual("autogen-ritual", ritual, "success", entropy_score)
        self._log_execution_report("autogen-ritual", ritual, entropy_score, results)

    def execute_vector(self, vector_name: str) -> bool:
        if vector_name not in VECTOR_REGISTRY:
            logger.error(f"Unregistered vector: {vector_name}")
            return False
        if not self._validate_platform(vector_name):
            return False
        if not self._check_dependencies(vector_name):
            return False
        if self.args.simulation and not is_simulation_safe(vector_name):
            logger.info(f"[{vector_name}] Skipped - not simulation-safe.")
            return False

        self._prompt_missing_args(vector_name)

        try:
            handler_func_name = VECTOR_REGISTRY[vector_name]
            handler = self.vector_handlers.get(handler_func_name)

            if not handler:
                logger.error(f"No dynamic handler loaded for vector: {vector_name} → {handler_func_name}")
                return False

            logger.info(f"Executing vector: {vector_name} via {handler_func_name}")
            handler(**vars(self.args))
            self.brain.update_vector_stats(vector_name, success=True)
            return True

        except Exception as ex:
            logger.error(f"[{vector_name}] Execution failed: {ex}")
            logger.debug(traceback.format_exc())
            return False

    def _log_execution_report(self, ritual_id, vectors, entropy, results):
        os.makedirs(os.path.dirname(self.args.telemetry_log), exist_ok=True)
        with open(self.args.telemetry_log, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "ritual_id": ritual_id,
                "vectors": vectors,
                "entropy_score": entropy,
                "results": [{"vector": v, "success": s} for v, s in results]
            }) + "\n")

    def interactive_shell(self):
        print("\nObserver CLI Ready. Commands: ritual, entropy, list, <vector>, exit")
        while True:
            try:
                cmd = input("phantom> ").strip()
                if cmd == "exit":
                    break
                elif cmd == "ritual":
                    self.run_single_ritual()
                elif cmd == "entropy":
                    stats = self.entropy.get_entropy_statistics()
                    print(f"Entropy avg={stats['average']:.2f}, count={stats['count']}")
                elif cmd == "list":
                    print("Available vectors:")
                    for v in self.vectors:
                        print(f" - {v}")
                elif cmd in self.vectors:
                    self.execute_vector(cmd)
                else:
                    print(f"Unknown command: {cmd}")
            except KeyboardInterrupt:
                print("\nTerminated by user.")
                break


def main():
    parser = build_parser()
    args = parser.parse_args()
    args = merge_args_with_config(args, load_config(args.config))

    logger.setLevel(getattr(logging, args.verbosity.upper(), logging.INFO))

    engine = phantomvector(args)

    if args.chain:
        RitualExecutor(engine).execute_chain(args.chain)
    elif args.list_chains:
        list_available_chains(RitualExecutor(engine))
    elif args.list_vectors:
        print("\nRegistered Vectors:")
        for v in list_all_vectors():
            meta = get_vector_metadata(v)
            print(f"- {v}: {meta['description']}")
    elif args.ritual:
        engine.run_single_ritual()
    elif args.shell:
        engine.interactive_shell()
    else:
        logger.info("No execution mode specified. Use --ritual, --shell, --chain, etc.")


if __name__ == "__main__":
    main()
