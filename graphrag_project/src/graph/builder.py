import networkx as nx
from typing import List, Optional
from ..models import Document, Entity, Relationship

class GraphBuilder:
    def __init__(self) -> None:
        self.graph = nx.Graph()
        
    def add_document(self, document: Document) -> None:
        for entity in document.entities:
            self.graph.add_node(
                entity.id,
                label=entity.label,
                type=entity.type,
                **entity.properties
            )
            
        for rel in document.relationships:
            self.graph.add_edge(
                rel.source_id,
                rel.target_id,
                type=rel.type,
                **rel.properties
            )
            
    def get_graph(self) -> nx.Graph:
        return self.graph
    
    def get_node_count(self) -> int:
        return self.graph.number_of_nodes()
        
    def get_edge_count(self) -> int:
        return self.graph.number_of_edges()
        
    def get_neighbors(self, node_id: str) -> List[str]:
        return list(self.graph.neighbors(node_id))
        
    def get_node(self, node_id: str) -> Optional[dict]:
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None