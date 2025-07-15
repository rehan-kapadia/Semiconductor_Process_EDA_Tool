from agent import SemiconductorProcessAgent
import os

def main():
    """
    Main entry point for running the Semiconductor Process Agent.
    """
    # --- Configuration ---
    # Neo4j connection details (use environment variables in production)
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASS = "password"

    # Input files
    script_dir = os.path.dirname(__file__)
    schematics_dir = os.path.abspath(os.path.join(script_dir, "..", "data", "input_schematics"))
    print(f"Looking for schematics in: {schematics_dir}")
    schematic_files = sorted([
        os.path.join(schematics_dir, f) for f in os.listdir(schematics_dir)
        if f.endswith('.png')
    ])

    # Create dummy input files if they don't exist
    if not os.path.exists(schematics_dir) or not schematic_files:
        print("Creating dummy input files for demonstration...")
        os.makedirs(schematics_dir, exist_ok=True)
        from perception.segmentation import SemanticSegmenter
        import cv2
        
        # Step 0: Substrate
        img0, _ = SemanticSegmenter.generate_synthetic_data()
        cv2.imwrite(os.path.join(schematics_dir, "step_0_substrate.png"), img0)
        
        # Step 1: Add Oxide
        img1, _ = SemanticSegmenter.generate_synthetic_data()
        # Redraw oxide to be on top of silicon
        cv2.rectangle(img1, (0, 154 - 20), (512, 154), (150, 200, 220), -1)
        cv2.imwrite(os.path.join(schematics_dir, "step_1_oxide.png"), img1)
        
        schematic_files = sorted([os.path.join(schematics_dir, f) for f in os.listdir(schematics_dir)])


    print(f"Found schematic files: {schematic_files}")

    # --- Agent Initialization and Execution ---
    agent = SemiconductorProcessAgent(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    agent.generate_flow(schematic_files)


if __name__ == "__main__":
    # Note: This script requires a running Neo4j database populated with the schema.
    # The perception modules also assume pre-trained models are available.
    # The provided code uses dummy models and data for a self-contained demonstration.
    import cv2 # Import here to be used in dummy data generation
    main()
