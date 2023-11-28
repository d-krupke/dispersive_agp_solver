import functools
import lzma
import tempfile
from pathlib import Path

import networkx as nx
import requests

from disp_agp_solver.instance import Instance, Position

# Data mapping instances names to urls
_db_file = Path(__file__).parent.absolute() / "sbgdb.json"


# cache of loaded instances
@functools.lru_cache(maxsize=32)
def fetch_as_nx(instance) -> nx.Graph:
    print("Downloading:", instance)
    with tempfile.TemporaryFile() as fp:
        data = requests.get(instance)
        # throw error if download failed
        data.raise_for_status()
        # Save file data to local copy
        fp.write(data.content)
        fp.seek(0)
        print("Parsing instance...")
        with lzma.open(fp) as xz:
            g = nx.read_graphml(xz)
            print(f"Parsed polygon with {g.number_of_nodes()} points.")
            return g


def integralize(g: nx.Graph, s: int):
    for n in g.nodes:
        g.nodes[n]["vertex-coordinate-x"] = round(
            s * float(g.nodes[n]["vertex-coordinate-x"])
        )
        g.nodes[n]["vertex-coordinate-y"] = round(
            s * float(g.nodes[n]["vertex-coordinate-y"])
        )


def _vertex_to_position(graph, vertex) -> Position:
    return (
        round(graph.nodes[vertex]["vertex-coordinate-x"]),
        round(graph.nodes[vertex]["vertex-coordinate-y"]),
    )


def graph_to_list(graph: nx.Graph):
    components = [
        [
            _vertex_to_position(graph, v)
            for v in nx.dfs_preorder_nodes(graph, source=next(iter(comp)))
        ]
        for comp in nx.connected_components(graph)
    ]
    if len(components) == 1:
        return components[0][::-1], []
    else:
        # move outer face to front
        components.sort(key=min)
        return components[0][::-1], components[1:]


def list_to_instance(outer_face, holes):
    positions = outer_face + sum(holes, [])
    position_to_index = {p: i for i, p in enumerate(positions)}
    boundary = [position_to_index[p] for p in outer_face]
    holes = [[position_to_index[p] for p in hole] for hole in holes]
    return Instance(positions, boundary, holes)


def fetch(instance) -> Instance:
    g = fetch_as_nx(instance)
    integralize(g, 10_000)
    outer_face, holes = graph_to_list(g)
    return list_to_instance(outer_face, holes)
