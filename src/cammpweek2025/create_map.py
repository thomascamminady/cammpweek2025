import warnings

import fire
import folium
import geopandas as gpd

from cammpweek2025.utils.logger import logger

warnings.filterwarnings(
    "ignore",
    message="Several features with id = .* have been found",
    category=RuntimeWarning,
    module="pyogrio.raw",
)


def main(
    edges_file: str = "data/streets_between_junctions.geojson",
    signals_file: str = "data/traffic_signals.geojson",
    stops_file: str = "data/stop_signs.geojson",
    map_file: str = "output/map.html",
):
    # 1) load edges & control‐nodes
    edges = gpd.read_file(edges_file)
    signals = gpd.read_file(signals_file)
    stops = gpd.read_file(stops_file)

    # 2) compute a "quality" column on edges
    def pick_quality(row):
        if row.get("smoothness"):
            return row["smoothness"]
        if row.get("surface"):
            return row["surface"]
        return "unknown"

    edges["quality"] = edges.apply(pick_quality, axis=1)

    # 3) color maps
    smooth_colors = {
        "excellent": "#2ca02c",
        "good": "#98df8a",
        "intermediate": "#ffbb78",
        "bad": "#ff7f0e",
        "very_bad": "#d62728",
    }
    surface_colors = {
        "asphalt": "#7f7f7f",
        "paved": "#c7c7c7",
        "unpaved": "#8c564b",
        "gravel": "#e377c2",
        "dirt": "#bcbd22",
    }
    default_color = "#444444"

    def style_function(feature):
        q = feature["properties"].get("quality", "")
        if q in smooth_colors:
            color = smooth_colors[q]
        elif q in surface_colors:
            color = surface_colors[q]
        else:
            color = default_color
        return {"color": color, "weight": 3, "opacity": 0.8}

    # 4) build map
    centroid = edges.geometry.union_all().centroid
    m = folium.Map(
        location=[centroid.y, centroid.x],
        zoom_start=13,
        tiles="CartoDB Positron",
        attr="&copy; CARTO",
    )

    # 5) prepare tooltip fields dynamically
    tooltip_fields = []
    tooltip_aliases = []
    if "name" in edges.columns:
        tooltip_fields.append("name")
        tooltip_aliases.append("Street name:")
    tooltip_fields.append("quality")
    tooltip_aliases.append("Quality:")

    tooltip = folium.GeoJsonTooltip(
        fields=tooltip_fields,
        aliases=tooltip_aliases,
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0F0F0;
            border: 1px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """,
    )

    # 6) add streets layer
    street_layer = folium.FeatureGroup(name="Streets by Quality")
    folium.GeoJson(
        edges,
        style_function=style_function,
        tooltip=tooltip,
        # fallback popup if no tooltip fields at all:
        popup=folium.GeoJsonPopup(fields=["osmid"], aliases=["OSM ID:"])
        if not tooltip_fields
        else None,
    ).add_to(street_layer)
    street_layer.add_to(m)

    # 7) add traffic signals & stops
    sig_layer = folium.FeatureGroup(name="Traffic signals")
    for _, row in signals.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color="yellow",
            fill=True,
            fill_color="yellow",
            popup="traffic signal",
        ).add_to(sig_layer)
    sig_layer.add_to(m)

    stop_layer = folium.FeatureGroup(name="Stop signs")
    for _, row in stops.iterrows():
        folium.RegularPolygonMarker(
            location=[row.geometry.y, row.geometry.x],
            number_of_sides=4,
            radius=6,
            color="red",
            fill=True,
            fill_color="red",
            popup="stop sign",
        ).add_to(stop_layer)
    stop_layer.add_to(m)

    # 8) layer control & save
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(map_file)
    logger.info(f"Saved map → {map_file}")


if __name__ == "__main__":
    fire.Fire(main)
