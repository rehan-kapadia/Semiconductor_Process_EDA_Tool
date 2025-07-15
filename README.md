# Semiconductor Process EDA Tool

## Overview

The Semiconductor Process EDA (Electronic Design Automation) Tool is an intelligent agent-based system designed to automate and optimize semiconductor manufacturing process flow generation. The system analyzes schematic diagrams of semiconductor device cross-sections at different manufacturing stages and automatically generates the corresponding process flow with optimized parameters.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Key Components](#key-components)
3. [How It Works](#how-it-works)
4. [Installation and Setup](#installation-and-setup)
5. [Usage](#usage)
6. [Technical Deep Dive](#technical-deep-dive)
7. [Dependencies](#dependencies)
8. [Future Enhancements](#future-enhancements)

## System Architecture

The tool follows a three-layer cognitive architecture inspired by robotics and AI systems:

```
┌─────────────────────────────────────────────────────┐
│                    AGENT LAYER                      │
│              (Main Orchestration)                   │
└─────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌───▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
│PERCEPTION│     │  COGNITIVE  │     │   ACTION    │
│  LAYER   │     │    LAYER    │     │   LAYER     │
├──────────┤     ├─────────────┤     ├─────────────┤
│•Register │     │•Knowledge   │     │•Optimizer   │
│•Segment  │     │  Graph      │     │•Mask Gen    │
│•Differ   │     │•Reasoning   │     │             │
└──────────┘     └─────────────┘     └─────────────┘
```

## Key Components

### 1. Perception Layer (`semiconductor_process_agent/perception/`)

The perception layer processes visual inputs (schematic images) to understand what changes occurred between manufacturing steps.

#### Components:
- **Image Registration** (`registration.py`): Aligns consecutive schematic images using ORB feature detection and homography transformation
- **Semantic Segmentation** (`segmentation.py`): Converts images into material maps using deep learning (U-Net architecture)
- **Difference Analysis** (`differencing.py`): Identifies and characterizes changes between material maps

### 2. Cognitive Layer (`semiconductor_process_agent/cognitive/`)

The cognitive layer performs reasoning and planning based on the perceived changes.

#### Components:
- **Knowledge Graph** (`knowledge_graph.py`): Interfaces with Neo4j database storing semiconductor manufacturing domain knowledge
- **Reasoning Engine** (`reasoning_engine.py`): Infers manufacturing processes from observed changes and plans appropriate actions

### 3. Action Layer (`semiconductor_process_agent/action/`)

The action layer executes the planned processes by generating optimized parameters and necessary files.

#### Components:
- **Process Optimizer** (`optimizer.py`): Uses surrogate modeling (Kriging) to find optimal process parameters
- **Mask Generator** (`mask_generator.py`): Extracts lithography masks from GDSII layout files

### 4. Main Agent (`semiconductor_process_agent/agent.py`)

The central orchestrator that implements the Sense-Plan-Act loop, coordinating all layers to generate complete process flows.

## How It Works

### Step-by-Step Process Flow

1. **Input Processing**
   - The system receives a sequence of schematic images showing the semiconductor device at different manufacturing stages
   - Images are expected to show cross-sectional views with different materials (silicon, oxide, metal, etc.)

2. **Perception Phase**
   - Images are aligned using feature-based registration to ensure spatial consistency
   - Each image is segmented to identify materials at the pixel level
   - Differences between consecutive images are analyzed to detect:
     - Material additions (depositions)
     - Material removals (etches)
     - Geometric characteristics (thickness, conformality, etc.)

3. **Cognitive Phase**
   - The reasoning engine analyzes the detected changes
   - Based on the type of change (addition/removal) and geometric profile, it infers the manufacturing process:
     - Conformal/planar additions → Deposition process
     - Anisotropic/isotropic removals → Etch process
   - The knowledge graph is queried to find compatible manufacturing tools
   - Constraints are applied (material compatibility, wafer size, tool availability)

4. **Action Phase**
   - For each identified process, the system:
     - Selects appropriate manufacturing tools
     - Optimizes process parameters (time, pressure) using surrogate models
     - Generates lithography masks if needed (for patterning steps)
   - Creates a complete process recipe with all parameters

5. **Output Generation**
   - The system outputs a JSON-formatted process flow containing:
     - Step numbers
     - Process types (etch, deposition, lithography)
     - Selected tools
     - Optimized recipe parameters

### Example Process Flow

```json
[
  {
    "step_number": 1,
    "process_type": "Deposition",
    "tool_id": "CVD_01",
    "recipe_parameters": {
      "time_s": 15.2,
      "pressure_torr": 1.8,
      "achieved_thickness_nm": 200.0
    }
  },
  {
    "step_number": 2,
    "process_type": "Lithography",
    "tool_id": "PHOTO_01",
    "recipe_parameters": {
      "mask_file": "output/mask_LITHO_STEP_2.gds",
      "resist_coat_recipe": "STANDARD_COAT_1UM",
      "exposure_recipe": "STANDARD_EXPOSE_200mJ",
      "develop_recipe": "STANDARD_DEV_60S"
    }
  }
]
```

## Installation and Setup

### Prerequisites

1. **Python Environment**
   - Python 3.8 or higher
   - Virtual environment (recommended)

2. **Neo4j Database**
   - Neo4j Community Edition or Enterprise
   - Default connection: `bolt://localhost:7687`
   - Credentials: username `neo4j`, password `password`

3. **System Dependencies**
   - OpenCV compatible system libraries
   - CUDA (optional, for GPU acceleration)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Semiconductor_PDA_Tool
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv PDAvenv
   source PDAvenv/bin/activate  # On Windows: PDAvenv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   cd semiconductor_process_agent
   pip install -r requirements.txt
   ```

4. Set up Neo4j database:
   - Install Neo4j from https://neo4j.com/download/
   - Start Neo4j service
   - Create database schema (see Knowledge Graph Setup section)

5. Prepare input data:
   - Place schematic images in `data/input_schematics/`
   - Place GDSII layouts in `data/input_layouts/` (if using lithography)

## Usage

### Basic Usage

Run the main script:
```bash
cd semiconductor_process_agent
python main.py
```

The system will:
1. Load schematic images from the input directory
2. Process them through the perception-cognitive-action pipeline
3. Output the generated process flow to console

### Custom Configuration

Modify `main.py` to customize:
- Neo4j connection parameters
- Input file paths
- Output destinations

### Programmatic Usage

```python
from agent import SemiconductorProcessAgent

# Initialize agent
agent = SemiconductorProcessAgent(
    kg_uri="bolt://localhost:7687",
    kg_user="neo4j",
    kg_pass="password"
)

# Generate process flow
schematic_files = ["step1.png", "step2.png", "step3.png"]
layout_files = {"LITHO_STEP_2": "layout.gds"}
agent.generate_flow(schematic_files, layout_files)
```

## Technical Deep Dive

### Material Recognition

The system recognizes 8 material types:
- 0: Vacuum/Air
- 1: Silicon (substrate)
- 2: Silicon Dioxide (oxide)
- 3: Polysilicon
- 4: Photoresist
- 5: Aluminum
- 6: Copper
- 7: Silicon Nitride

### Process Inference Rules

The reasoning engine uses rule-based inference:

**For Depositions:**
- Conformal profile (aspect ratio > 5) → Likely CVD process
- Planar profile → Likely PVD or spin-coating

**For Etches:**
- Anisotropic profile (aspect ratio < 0.5) → Likely RIE or ion milling
- Isotropic profile → Likely wet etch or isotropic plasma

### Optimization Algorithm

The process optimizer uses:
- **Surrogate Model**: Kriging (Gaussian Process regression)
- **Optimization Method**: L-BFGS-B (bounded optimization)
- **Parameters**: Time (5-30 seconds), Pressure (0.5-3.0 Torr)
- **Objective**: Minimize difference between target and achieved thickness

### Knowledge Graph Schema

The Neo4j database uses this schema:

```cypher
// Nodes
(:Tool {tool_id, name, status, wafer_size, surrogate_model_path})
(:Process {category})
(:Material {name})

// Relationships
(Tool)-[:CAN_PERFORM]->(Process)
(Process)-[:PROCESSES]->(Material)
(Tool)-[:INCOMPATIBLE_WITH]->(Material)
```

## Dependencies

Core dependencies from `requirements.txt`:
- **numpy**: Numerical computations
- **opencv-python**: Image processing
- **scikit-image**: Advanced image processing
- **torch, torchvision**: Deep learning framework
- **neo4j**: Graph database driver
- **gdspy**: GDSII file manipulation
- **smt**: Surrogate modeling toolbox
- **scipy**: Scientific computing
- **Pillow**: Image I/O

## Future Enhancements

### Planned Features

1. **Enhanced Process Recognition**
   - Support for ion implantation
   - Chemical mechanical polishing (CMP)
   - Thermal processes (oxidation, annealing)

2. **Advanced Optimization**
   - Multi-objective optimization
   - Process window optimization
   - Yield prediction integration

3. **Improved Perception**
   - 3D structure recognition
   - Multi-scale feature detection
   - Uncertainty quantification

4. **Extended Knowledge Base**
   - More tool models
   - Material property database
   - Process-structure-property relationships

5. **User Interface**
   - Web-based visualization
   - Interactive process flow editing
   - Real-time optimization feedback

### Architecture Extensions

- **Feedback Loop**: Integrate metrology data for closed-loop optimization
- **Multi-Agent System**: Parallel processing for complex devices
- **Cloud Deployment**: Scalable processing for large design libraries

## Contributing

This tool is designed as a research prototype demonstrating the application of AI techniques to semiconductor process automation. Contributions in the following areas are welcome:
- Process model improvements
- Knowledge graph extensions
- New material recognition capabilities
- Optimization algorithm enhancements

## License

[License information to be added]

## Contact

[Contact information to be added]