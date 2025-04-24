# ruff: noqa: N806

import fire

from cammpweek2025.utils.create_graph import create_graph
from cammpweek2025.utils.logger import logger


def main(
    edges_file: str = "data/streets_between_junctions.geojson",
    signals_file: str = "data/traffic_signals.geojson",
    stops_file: str = "data/stop_signs.geojson",
):
    G = create_graph(
        edges_file=edges_file,
        signals_file=signals_file,
        stops_file=stops_file,
    )

    logger.info("Sample edges with attributes:")
    for u, v, data in list(G.edges(data=True))[:5]:
        print(f"Edge {u}->{v}:")
        for key, val in data.items():
            logger.info(f"  {key}: {val}")
        logger.info("")

    # log summary
    logger.info(
        f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges."
    )


if __name__ == "__main__":
    fire.Fire(main)
