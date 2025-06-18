import networkx as nx
import json
from pathlib import Path
from typing import Optional

class GraphStorage:
    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def save_graph(self, graph: nx.Graph, name: str) -> None:
        data = nx.node_link_data(graph)
        file_path = self.storage_dir / f"{name}.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
            
    def load_graph(self, name: str) -> Optional[nx.Graph]:
        file_path = self.storage_dir / f"{name}.json"
        if not file_path.exists():
            return None
            
        with open(file_path) as f:
            data = json.load(f)
            
        return nx.node_link_graph(data)
        
    def list_graphs(self) -> list[str]:
        return [f.stem for f in self.storage_dir.glob("*.json")]
        
    def delete_graph(self, name: str) -> bool:
        file_path = self.storage_dir / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False