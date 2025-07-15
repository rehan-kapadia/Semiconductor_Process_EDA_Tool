from typing import List, Dict, Any
from .knowledge_graph import KnowledgeGraphConnector

class ReasoningEngine:
    """
    Infers process steps and queries the KG for candidate tools.
    """
    def __init__(self, kg_connector: KnowledgeGraphConnector):
        self.kg = kg_connector
        print("COGNITIVE: Reasoning Engine initialized.")

    def plan_step(self, changes: List[Dict[str, Any]], wafer_state: Dict) -> Dict:
        """
        Takes perceptual changes and plans the next manufacturing step.

        Args:
            changes (List[Dict[str, Any]]): The list of changes from the Perception Layer.
            wafer_state (Dict): Current state of the wafer, including materials present.

        Returns:
            Dict: A plan containing the process, material, and candidate tools.
        """
        if not changes:
            return {"status": "NO_CHANGE", "plan": None}

        # For simplicity, we process the first major change.
        # A real system might handle multiple simultaneous changes.
        change = changes[0]
        print(f"COGNITIVE: Reasoning about change: {change}")

        # --- Rule-Based Process Inference ---
        inferred_process = self._infer_process(change)
        if not inferred_process:
            return {"status": "FAILED_INFERENCE", "plan": None}
        
        print(f"COGNITIVE: Inferred process: {inferred_process}")

        # --- KG Query for Tool Candidates ---
        candidate_tools = self.kg.find_capable_tools(
            process_category=inferred_process['category'],
            material_name=inferred_process['material'],
            wafer_size=wafer_state['size']
        )
        print(f"COGNITIVE: Found {len(candidate_tools)} initial candidates.")

        # --- Constraint Filtering ---
        valid_tools = []
        for tool in candidate_tools:
            is_incompatible = self.kg.check_incompatibility(tool['tool_id'], wafer_state['materials_present'])
            if not is_incompatible:
                valid_tools.append(tool)
            else:
                print(f"COGNITIVE: Filtering out tool '{tool['tool_id']}' due to material incompatibility.")
        
        if not valid_tools:
            return {"status": "NO_VALID_TOOLS", "plan": None}
        
        plan = {
            "process_category": inferred_process['category'],
            "target_material": inferred_process['material'],
            "target_geometry": {k: v for k, v in change.items() if k in ['thickness', 'width']},
            "candidate_tools": valid_tools
        }
        
        return {"status": "SUCCESS", "plan": plan}

    def _infer_process(self, change: Dict) -> Dict:
        """A simple rule-based inference function."""
        change_type = change['change_type']
        profile = change['profile']
        material = change['material_id']

        if change_type == 'addition':
            # Rule for Deposition
            if profile in ['conformal', 'planar']:
                return {'category': 'Deposition', 'material': material}
        elif change_type == 'removal':
            # Rule for Etching
            if profile in ['anisotropic', 'isotropic']:
                return {'category': 'Etch', 'material': material}
        
        # Add more rules for litho, implant, etc. here
        
        return None
