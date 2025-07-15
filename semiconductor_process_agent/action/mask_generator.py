import gdspy
from typing import Tuple

def generate_mask_file(input_gds: str, output_gds: str, layer_datatype: Tuple[int, int]):
    """
    Extracts a specific layer from an input GDSII file and saves it as a new mask file.

    Args:
        input_gds (str): Path to the input layout GDSII file.
        output_gds (str): Path to save the new mask GDSII file.
        layer_datatype (Tuple[int, int]): The (layer, datatype) tuple to extract.
    """
    print(f"ACTION [Mask Gen]: Generating mask for layer {layer_datatype} from '{input_gds}'")
    
    # Load the library
    gdsii = gdspy.GdsLibrary(infile=input_gds)
    main_cell = gdsii.top_level()[0]

    # Create a new cell for the mask layer
    mask_cell = gdspy.Cell(f"MASK_{layer_datatype[0]}_{layer_datatype[1]}")

    # Get all polygons from the specified layer
    polygons = main_cell.get_polygons(by_spec=True).get(layer_datatype, [])

    if not polygons:
        print(f"WARNING: No polygons found on layer {layer_datatype}.")
        return

    mask_cell.add(polygons)

    # Write the new GDSII file containing only the mask cell
    gdspy.write_gds(output_gds, cells=[mask_cell], unit=gdsii.unit, precision=gdsii.precision)
    
    print(f"ACTION [Mask Gen]: Mask file saved to '{output_gds}'")
