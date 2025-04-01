import fire
import folium
import polars as pl


def plot(df_road_path: str, df_points_of_interest_path: str) -> None:
    df_roads = pl.read_parquet(df_road_path)
    df_points_of_interest = pl.read_parquet(df_points_of_interest_path)
    # create a map object and then add the lines
    m = folium.Map()

    for row in df_roads.iter_rows(named=True):
        coordinates = row["geometry_coordinates"]
        # create a PolyLine object

        polyline = folium.PolyLine(
            locations=coordinates,
            color="blue",
            weight=2,
            opacity=1,
        )
        # add the PolyLine object to the map
        polyline.add_to(m)

    for row in df_points_of_interest.iter_rows(named=True):
        point = row["geometry_coordinates"]
        # create a dot on the map
        dot = folium.CircleMarker(
            location=point,
            radius=5,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.6,
        )
        # add the dot to the map
        dot.add_to(m)

    # Set bounding box to be 49-51 and 8 to 9
    m.fit_bounds([[50.72, 7.0], [50.74, 7.2]])

    # save the map to an HTML file
    m.save("output/lines.html")


if __name__ == "__main__":
    fire.Fire(plot)
