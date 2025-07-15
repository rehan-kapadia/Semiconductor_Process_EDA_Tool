import cv2
import numpy as np
from typing import List, Dict, Any
from .segmentation import ID_TO_MATERIAL

class SchematicDiffer:
    """
    Analyzes two material maps to find and quantify the differences.
    """

    def analyze_difference(self, map1: np.ndarray, map2: np.ndarray) -> List[Dict[str, Any]]:
        """
        Calculates the difference between two material maps and extracts geometric features.

        Args:
            map1 (np.ndarray): The material map for the initial state (step_N).
            map2 (np.ndarray): The material map for the final state (step_N+1).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each describing a detected change.
        """
        print("PERCEPTION: Analyzing material map differences...")
        if map1.shape != map2.shape:
            raise ValueError("Material maps must have the same dimensions.")

        # Calculate the delta map
        delta_map = map2.astype(np.int16) - map1.astype(np.int16)
        
        changes = []
        
        # Analyze additions
        added_materials = np.unique(delta_map[delta_map > 0])
        for mat_id in added_materials:
            changes.extend(self._extract_features(delta_map, mat_id, 'addition'))
            
        # Analyze removals
        removed_materials = np.unique(delta_map[delta_map < 0])
        for mat_id in removed_materials:
            # The material ID in the delta map is negative, so we use the original map
            # to find what material was there before.
            original_mat_id = map1[delta_map == mat_id][0]
            changes.extend(self._extract_features(delta_map, mat_id, 'removal', original_mat_id))

        print(f"PERCEPTION: Found {len(changes)} distinct changes.")
        return changes

    def _extract_features(self, delta_map: np.ndarray, value: int, change_type: str, original_mat_id=None) -> List[Dict[str, Any]]:
        """
        Extracts features for all blobs of a specific value in the delta map.
        """
        mask = np.where(delta_map == value, 255, 0).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        extracted_features = []
        for contour in contours:
            if cv2.contourArea(contour) < 10: # Ignore tiny noise
                continue

            x, y, w, h = cv2.boundingRect(contour)
            
            # Determine profile (simple heuristic)
            aspect_ratio = w / h
            profile = 'unknown'
            if change_type == 'removal':
                profile = 'anisotropic' if aspect_ratio < 0.5 else 'isotropic'
            elif change_type == 'addition':
                profile = 'conformal' if aspect_ratio > 5 else 'planar'

            mat_id = value if change_type == 'addition' else original_mat_id
            
            feature = {
                'change_type': change_type,
                'material_id': ID_TO_MATERIAL.get(mat_id, 'unknown'),
                'area': cv2.contourArea(contour),
                'bounding_box': (x, y, w, h),
                'thickness': h,
                'width': w,
                'profile': profile
            }
            extracted_features.append(feature)
        
        return extracted_features
