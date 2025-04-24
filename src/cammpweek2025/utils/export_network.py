# ruff: noqa: N806
import os
import shutil

import fire
import geopandas as gpd
import networkx as nx
import osmnx as ox

from cammpweek2025.utils.logger import logger


def main(
    geometry_file: str = "data/streets_between_junctions.geojson",
    signals_file: str = "data/traffic_signals.geojson",
    stops_file: str = "data/stop_signs.geojson",
):
    # 1) build your street‐between‐junctions network as before…
    ox.settings.useful_tags_way += ["surface", "smoothness"]  # type: ignore
    west, south, east, north = 7.06, 50.70, 7.15, 50.77
    bbox = (west, south, east, north)
    custom_filter = '["highway"~"^(residential|unclassified|tertiary|secondary|primary|cycleway)$"]'
    G = ox.graph_from_bbox(
        bbox=bbox,
        custom_filter=custom_filter,
        simplify=False,
        retain_all=False,
    )
    G = ox.simplify_graph(G)
    # peel off all degree < 2…
    while True:
        to_remove = [n for n, d in G.degree() if d < 2]  # type: ignore
        if not to_remove:
            break
        G.remove_nodes_from(to_remove)

    # remove all hanging roads (nodes with <2 connections) at once via the 2-core
    G.remove_edges_from(nx.selfloop_edges(G))
    G_undir = nx.Graph(G.to_undirected())
    core_nodes = nx.k_core(G_undir, k=2).nodes()
    G = G.subgraph(core_nodes).copy()

    # export the edges
    nodes, edges = ox.graph_to_gdfs(G)
    # flatten any list-valued tags and cast to string
    for tag in [
        "osmid",
        "highway",
        "surface",
        "smoothness",
        "maxspeed",
        "name",
        "lanes",
        "width",
    ]:
        if tag in edges.columns:
            edges[tag] = edges[tag].apply(
                lambda v: v[0] if isinstance(v, (list, tuple)) else v
            )
            edges[tag] = edges[tag].fillna("").astype(str)
    edges.to_file(geometry_file, driver="GeoJSON")
    logger.info(f"Exported network → {geometry_file}")

    # 2) now pull out traffic signals & stop signs as point layers
    #    (OSMnx will grab any geometry with highway=traffic_signals or =stop)
    tags = {"highway": ["traffic_signals", "stop"]}
    gdf = ox.features_from_bbox(bbox=bbox, tags=tags)  # type: ignore

    # split them out and write
    gdf_signals = gdf[gdf["highway"] == "traffic_signals"]
    gdf_stops = gdf[gdf["highway"] == "stop"]

    # make sure everything is in the same CRS
    edges = edges.to_crs(gdf_signals.crs)  # type: ignore

    # spatial‐join: keep only points that intersect any edge
    gdf_signals = gpd.sjoin(
        gdf_signals, edges[["geometry"]], predicate="intersects", how="inner"
    ).drop(columns=["index_right"], errors="ignore")

    gdf_stops = gpd.sjoin(
        gdf_stops, edges[["geometry"]], predicate="intersects", how="inner"
    ).drop(columns=["index_right"], errors="ignore")

    gdf_signals.to_file(signals_file, driver="GeoJSON")
    gdf_stops.to_file(stops_file, driver="GeoJSON")
    logger.info(f"Exported {len(gdf_signals)} signals → {signals_file}")
    logger.info(f"Exported {len(gdf_stops)} stops   → {stops_file}")

    # 3) clean up cache
    if os.path.exists("cache"):
        for fn in os.listdir("cache"):
            p = os.path.join("cache", fn)
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.unlink(p)
            except Exception as e:
                logger.error(f"couldn't delete {p}: {e}")


if __name__ == "__main__":
    fire.Fire(main)
