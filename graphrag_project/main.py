import click
from pathlib import Path
from src.models import Document, Entity, Relationship
from src.graph.builder import GraphBuilder
from src.graph.storage import GraphStorage
import networkx as nx
import matplotlib.pyplot as plt

@click.group()
def cli():
    """GraphRAG CLI for managing knowledge graphs"""
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('graph_name')
def ingest(input_file: str, graph_name: str):
    """Ingest a document and create a knowledge graph"""
    content = Path(input_file).read_text()
    
    # Demo entities and relationships
    doc = Document(
        id="doc1",
        content=content,
        metadata={"source": input_file},
        entities=[
            Entity(id="e1", label="Example", type="concept", properties={}),
            Entity(id="e2", label="Demo", type="concept", properties={})
        ],
        relationships=[
            Relationship(source_id="e1", target_id="e2", type="related_to", properties={})
        ]
    )
    
    builder = GraphBuilder()
    builder.add_document(doc)
    
    storage = GraphStorage("data/graphs")
    storage.save_graph(builder.get_graph(), graph_name)
    click.echo(f"Created graph '{graph_name}' with {builder.get_node_count()} nodes")

@cli.command()
@click.argument('graph_name')
def visualize(graph_name: str):
    """Visualize a knowledge graph"""
    storage = GraphStorage("data/graphs")
    graph = storage.load_graph(graph_name)
    
    if not graph:
        click.echo(f"Graph '{graph_name}' not found")
        return
        
    plt.figure(figsize=(12, 8))
    nx.draw(graph, with_labels=True, node_color='lightblue', 
            node_size=1500, font_size=10)
    plt.savefig(f"{graph_name}.png")
    click.echo(f"Graph visualization saved as {graph_name}.png")

@cli.command()
@click.argument('graph_name')
def stats(graph_name: str):
    """Show graph statistics"""
    storage = GraphStorage("data/graphs")
    graph = storage.load_graph(graph_name)
    
    if not graph:
        click.echo(f"Graph '{graph_name}' not found")
        return
        
    click.echo(f"Graph: {graph_name}")
    click.echo(f"Nodes: {graph.number_of_nodes()}")
    click.echo(f"Edges: {graph.number_of_edges()}")
    click.echo(f"Density: {nx.density(graph):.4f}")

if __name__ == '__main__':
    cli()