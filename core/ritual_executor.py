# core/ritual_executor.py

import os
import yaml
import logging
from typing import List, Dict, Any
from core.vector_registry import validate_vector_chain, requires_arguments

logger = logging.getLogger("RitualExecutor")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class RitualExecutor:
    """
    Loads, validates, and executes YAML-defined ritual chains based on environment state.
    """

    def __init__(self, engine, chains_path: str = "ops/ritual_chains.yaml"):
        self.engine = engine
        self.chain_path = chains_path
        self.ritual_chains: List[Dict[str, Any]] = self._load_chains()

    def _load_chains(self) -> List[Dict[str, Any]]:
        """
        Load ritual chains from YAML file.
        """
        if not os.path.exists(self.chain_path):
            logger.error(f"Ritual chains file not found: {self.chain_path}")
            return []

        with open(self.chain_path, "r") as f:
            chains = yaml.safe_load(f)

        valid_chains = []
        for chain in chains:
            if not validate_vector_chain(chain["vectors"]):
                logger.warning(f"Invalid vector(s) in chain '{chain['id']}': {chain['vectors']}")
                continue
            valid_chains.append(chain)
        logger.info(f"{len(valid_chains)} valid ritual chains loaded.")
        return valid_chains

    def get_chain_by_id(self, chain_id: str) -> Dict[str, Any]:
        """
        Retrieve a ritual chain by its ID.
        """
        for chain in self.ritual_chains:
            if chain["id"] == chain_id:
                return chain
        raise ValueError(f"Chain '{chain_id}' not found.")

    def _check_required_args(self, chain: Dict[str, Any]) -> bool:
        """
        Ensure all required inputs for a chain are satisfied in args.
        """
        for key in chain.get("required", []):
            if not getattr(self.engine.args, key, None):
                logger.error(f"Missing required input for chain: {key}")
                return False
        return True

    def _check_entropy_threshold(self, chain: Dict[str, Any]) -> bool:
        """
        Ensure current entropy score meets minimum threshold.
        """
        current_entropy = self.engine.entropy.state.current_score
        min_required = chain.get("min_entropy", 0.0)
        if current_entropy < min_required:
            logger.warning(
                f"Entropy too low for chain '{chain['id']}' "
                f"(current: {current_entropy:.2f}, required: {min_required})"
            )
            return False
        return True

    def execute_chain(self, chain_id: str):
        """
        Validate and execute a ritual chain by ID.
        """
        try:
            chain = self.get_chain_by_id(chain_id)
        except ValueError as e:
            logger.error(str(e))
            return

        logger.info(f"Executing ritual chain: {chain['name']}")
        logger.info(f"Description: {chain.get('description', 'No description provided')}")

        if not self._check_required_args(chain):
            logger.error("Aborting execution: missing arguments.")
            return

        if not self._check_entropy_threshold(chain):
            logger.error("Aborting execution: entropy conditions not met.")
            return

        for vector_id in chain["vectors"]:
            try:
                self.engine.execute_vector(vector_id)
            except Exception as ex:
                logger.error(f"Vector execution failed: {vector_id} → {str(ex)}")

        logger.info(f"Chain '{chain['id']}' execution complete.")


def list_available_chains(executor: RitualExecutor):
    """
    Print a list of chains with basic info.
    """
    print("\nAvailable Ritual Chains:")
    for chain in executor.ritual_chains:
        print(f" - ID: {chain['id']}")
        print(f"   Name: {chain['name']}")
        print(f"   Tags: {', '.join(chain.get('tags', []))}")
        print(f"   Requires: {', '.join(chain.get('required', [])) or 'None'}")
        print(f"   Entropy: ≥ {chain.get('min_entropy', 0.0)}")
        print()
