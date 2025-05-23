import os
import importlib
import logging

logger = logging.getLogger("AttackLoader")

ATTACKS_PATH = "attacks"
VECTOR_HANDLERS = {}

def load_all_attacks():
    """
    Dynamically import all Python files in the attacks directory and register handlers.
    """
    for filename in os.listdir(ATTACKS_PATH):
        if filename.startswith("_") or not filename.endswith(".py"):
            continue

        module_name = filename[:-3]
        module_path = f"{ATTACKS_PATH}.{module_name}"

        try:
            module = importlib.import_module(module_path)

            # Convention: handler is always named after file (e.g., rf_blend_attack in rf_layer_blend.py)
            for attr in dir(module):
                if attr.endswith("_attack") or attr.endswith("_injector") or attr.endswith("_sim"):
                    VECTOR_HANDLERS[attr] = getattr(module, attr)

        except Exception as e:
            logger.warning(f"Failed to import {module_path}: {e}")

    logger.info(f"[AttackLoader] Loaded {len(VECTOR_HANDLERS)} attack handlers.")
    return VECTOR_HANDLERS
