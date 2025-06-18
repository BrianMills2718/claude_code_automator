from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Entity:
    id: str
    label: str
    type: str
    properties: Dict[str, str]

@dataclass
class Relationship:
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, str]

@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, str]
    entities: List[Entity]
    relationships: List[Relationship]