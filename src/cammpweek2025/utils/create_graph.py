# ruff: noqa: N806
import warnings

import geopandas as gpd
import networkx as nx

warnings.filterwarnings(
    "ignore",
    message="Several features with id = .* have been found",
    category=RuntimeWarning,
    module="pyogrio.raw",
)


def create_graph(
    edges_file: str = "data/streets_between_junctions.geojson",
    signals_file: str = "data/traffic_signals.geojson",
    stops_file: str = "data/stop_signs.geojson",
) -> nx.DiGraph:
    # 1) load GeoJSONs
    edges = gpd.read_file(edges_file)
    signals = gpd.read_file(signals_file)
    stops = gpd.read_file(stops_file)

    # 2) reset index to have a stable edge identifier
    edges = edges.reset_index(drop=False).rename(
        columns={"index": "edge_index"}
    )

    # 3) spatially join signals & stops to edges
    #    keep only those that intersect any edge
    signals_on_edges = gpd.sjoin(
        signals,
        edges[["edge_index", "geometry"]],
        predicate="intersects",
        how="inner",
    )
    stops_on_edges = gpd.sjoin(
        stops,
        edges[["edge_index", "geometry"]],
        predicate="intersects",
        how="inner",
    )

    # 4) count per edge
    sig_counts = signals_on_edges.groupby("edge_index").size()
    stop_counts = stops_on_edges.groupby("edge_index").size()

    edges["n_traffic_signals"] = (
        edges["edge_index"].map(sig_counts).fillna(0).astype(int)
    )
    edges["n_stop_signs"] = (
        edges["edge_index"].map(stop_counts).fillna(0).astype(int)
    )

    # 5) build NetworkX directed graph
    G = nx.DiGraph()

    # collect node coordinates from edge endpoints
    node_coords: dict[int, tuple[float, float]] = {}
    for _, row in edges.iterrows():
        u = int(row["u"])
        v = int(row["v"])
        coords = row.geometry.coords
        node_coords.setdefault(u, coords[0])
        node_coords.setdefault(v, coords[-1])

    # add nodes with position attributes
    for node_id, (x, y) in node_coords.items():
        G.add_node(node_id, x=x, y=y)

    # add edges with all attributes
    for _, row in edges.iterrows():
        u = int(row["u"])
        v = int(row["v"])
        attr = row.drop(["edge_index", "geometry"]).to_dict()
        G.add_edge(u, v, **attr)

    return G
