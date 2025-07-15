from perception.registration import ImageRegistrar
from perception.segmentation import SemanticSegmenter
from perception.differencing import SchematicDiffer
from cognitive.knowledge_graph import KnowledgeGraphConnector
from cognitive.reasoning_engine import ReasoningEngine
from action.optimizer import ProcessOptimizer
from action.mask_generator import generate_mask_file
import os
import cv2

class SemiconductorProcessAgent:
    """
    The main agent that orchestrates the entire process flow generation.
    """
    def __init__(self, kg_uri, kg_user, kg_pass):
        # Initialize all layers
        self.registrar = ImageRegistrar()
        self.segmenter = SemanticSegmenter() # Assumes a pre-trained model exists
        self.differ = SchematicDiffer()
        self.kg_connector = KnowledgeGraphConnector(kg_uri, kg_user, kg_pass)
        self.reasoner = ReasoningEngine(self.kg_connector)
        self.optimizer = ProcessOptimizer()

        self.wafer_state = {
            "size": 300,
            "materials_present": ["silicon"] # Start with a bare silicon wafer
        }
        self.process_flow = []

    def generate_flow(self, schematic_files: list, layout_files: dict = {}):
        """
        Runs the full Sense-Plan-Act loop for a sequence of schematics.

        Args:
            schematic_files (list): A list of paths to schematic PNG files in order.
            layout_files (dict): A map from process step name to GDSII layout file path.
        """
        for i in range(len(schematic_files) - 1):
            step_n_path = schematic_files[i]
            step_n1_path = schematic_files[i+1]
            
            print(f"\n--- Processing Transition: Step {i} -> Step {i+1} ---")
            
            # --- SENSE ---
            aligned_n1_img = self.registrar.align_images(step_n_path, step_n1_path)
            step_n_img = cv2.imread(step_n_path)
            
            map_n = self.segmenter.segment_image(step_n_img)
            map_n1 = self.segmenter.segment_image(aligned_n1_img)
            
            changes = self.differ.analyze_difference(map_n, map_n1)

            # --- PLAN ---
            result = self.reasoner.plan_step(changes, self.wafer_state)
            
            if result['status'] != 'SUCCESS':
                print(f"AGENT ERROR: Planning failed with status: {result['status']}")
                break
            
            plan = result['plan']
            
            # --- ACT ---
            # Final tool selection (simple heuristic: pick first valid tool)
            selected_tool = plan['candidate_tools'][0]
            print(f"ACTION: Selected tool '{selected_tool['tool_id']}' for process '{plan['process_category']}'")

            recipe = {}
            if plan['process_category'] == 'Lithography':
                # Handle lithography step and mask generation
                step_name = f"LITHO_STEP_{i+1}"
                if step_name in layout_files:
                    output_mask_path = os.path.join("output", f"mask_{step_name}.gds")
                    # Assume layer/datatype is known or inferred
                    generate_mask_file(layout_files[step_name], output_mask_path, (10, 0))
                    recipe['mask_file'] = output_mask_path
                recipe['resist_coat_recipe'] = 'STANDARD_COAT_1UM'
                recipe['exposure_recipe'] = 'STANDARD_EXPOSE_200mJ'
                recipe['develop_recipe'] = 'STANDARD_DEV_60S'
            else:
                # Handle other processes with optimization
                recipe = self.optimizer.optimize(
                    model_path=selected_tool['model_path'],
                    target_geometry=plan['target_geometry']
                )

            # --- Record Step and Update State ---
            process_step = {
                "step_number": i + 1,
                "process_type": plan['process_category'],
                "tool_id": selected_tool['tool_id'],
                "recipe_parameters": recipe
            }
            self.process_flow.append(process_step)
            self.wafer_state['materials_present'].append(plan['target_material'])
            # Remove duplicates
            self.wafer_state['materials_present'] = list(set(self.wafer_state['materials_present']))

        print("\n--- FINAL GENERATED PROCESS FLOW ---")
        import json
        print(json.dumps(self.process_flow, indent=2))
        
        self.kg_connector.close()
