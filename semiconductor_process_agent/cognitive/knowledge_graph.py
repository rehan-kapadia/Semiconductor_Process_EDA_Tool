from neo4j import GraphDatabase
from typing import List, Dict, Any

class KnowledgeGraphConnector:
    """
    Manages connection and queries to the Neo4j Knowledge Graph.
    """
    def __init__(self, uri, user, password):
        """
        Initializes the database driver.
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print("COGNITIVE [KG]: Knowledge Graph connector initialized.")

    def close(self):
        self.driver.close()

    def find_capable_tools(self, process_category: str, material_name: str, wafer_size: int) -> List[Dict[str, Any]]:
        """
        Finds tools that can perform a specific process category on a material.

        Args:
            process_category (str): e.g., 'Etch', 'Deposition'.
            material_name (str): The name of the material being affected.
            wafer_size (int): The required wafer size (e.g., 300).

        Returns:
            List[Dict[str, Any]]: A list of tool dictionaries.
        """
        query = """
        MATCH (t:Tool)-->(p:Process)-->(m:Material)
        WHERE p.category = $category
          AND m.name = $material
          AND t.status = 'online'
          AND t.wafer_size = $wafer_size
        RETURN t.tool_id AS tool_id, t.name AS tool_name, t.surrogate_model_path as model_path
        """
        with self.driver.session() as session:
            results = session.run(query, category=process_category, material=material_name, wafer_size=wafer_size)
            return [record.data() for record in results]

    def check_incompatibility(self, tool_id: str, processed_materials: List[str]) -> bool:
        """
        Checks if a tool is incompatible with any material already on the wafer.

        Args:
            tool_id (str): The ID of the tool to check.
            processed_materials (List[str]): List of material names on the wafer.

        Returns:
            bool: True if an incompatibility exists, False otherwise.
        """
        query = """
        MATCH (t:Tool {tool_id: $tool_id})-->(m:Material)
        WHERE m.name IN $processed_materials
        RETURN count(m) > 0 AS incompatible
        """
        with self.driver.session() as session:
            result = session.run(query, tool_id=tool_id, processed_materials=processed_materials).single()
            return result['incompatible'] if result else False
