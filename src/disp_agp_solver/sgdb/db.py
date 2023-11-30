import json
import lzma
import re
from pathlib import Path

import networkx as nx
import requests

from ..instance import Instance

# Data mapping instances names to urls
_db_file = Path(__file__).parent.absolute() / "sbgdb.json"


def _integralize(g: nx.Graph, s: int):
    for n in g.nodes:
        g.nodes[n]["vertex-coordinate-x"] = round(
            s * float(g.nodes[n]["vertex-coordinate-x"])
        )
        g.nodes[n]["vertex-coordinate-y"] = round(
            s * float(g.nodes[n]["vertex-coordinate-y"])
        )


def _vertex_to_position(graph, vertex):
    return (
        round(graph.nodes[vertex]["vertex-coordinate-x"]),
        round(graph.nodes[vertex]["vertex-coordinate-y"]),
    )


def _graph_to_list(graph: nx.Graph):
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


def _list_to_instance(outer_face, holes):
    positions = outer_face + sum(holes, [])
    position_to_index = {p: i for i, p in enumerate(positions)}
    boundary = [position_to_index[p] for p in outer_face]
    holes = [[position_to_index[p] for p in hole] for hole in holes]
    return Instance(positions, boundary, holes)


class SalzburgPolygonDataBase:
    def __init__(self):
        with open(_db_file) as f:
            self._urls = json.load(f)
        self._cache_folder = Path("./_salzburg_polygon_database_cache/")

    def get_size_from_url(self, instance_url):
        # the url looks like this: https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/srpg_perturbed_smr/srpg_smr9957440.graphml.xz
        # the number at the end is the size
        assert instance_url.endswith(".graphml.xz")
        instance_url_short = instance_url.split("/")[-1][: -len(".graphml.xz")]
        match = re.search(r"(?P<size>\d+)_\d+$", instance_url_short)
        if match:
            return int(match.group("size"))
        # extract digits from the end of the string using regex
        match = re.search(r"\d+$", instance_url_short)
        assert match, f"{instance_url} does not end with a number"
        return int(match.group())

    def get_name_from_url(self, instance_url):
        return str(instance_url).split("/")[-1][: -len(".graphml.xz")]

    def get_download_path(self, instance_url):
        return self._cache_folder / (
            self.get_name_from_url(instance_url) + ".graphml.xz"
        )

    def download(self, instance_url):
        # download the instance
        download_path = self.get_download_path(instance_url)
        if not self._cache_folder.exists():
            self._cache_folder.mkdir()
        with download_path.open("wb") as f:
            data = requests.get(instance_url)
            # throw error if download failed
            data.raise_for_status()
            # Save file data to local copy
            f.write(data.content)

    def iter_range(self, min_size, max_size):
        for url in self._urls["sbgdb-20200507"]:
            size = self.get_size_from_url(url)
            if min_size <= size <= max_size:
                yield url

    def __getitem__(self, instance_url):
        # check if the instance is already downloaded
        if not self.get_download_path(instance_url).exists():
            self.download(instance_url)
        with open(self.get_download_path(instance_url), "rb") as fp:
            with lzma.open(fp) as xz:
                g = nx.read_graphml(xz)
                return self._convert(g)

    def _convert(self, g: nx.Graph):
        # integralize
        _integralize(g, 1000)
        # convert to list representation
        outer_face, holes = _graph_to_list(g)
        # convert to instance
        return _list_to_instance(outer_face, holes)

    def __iter__(self):
        return iter(self._urls["sbgdb-20200507"])
