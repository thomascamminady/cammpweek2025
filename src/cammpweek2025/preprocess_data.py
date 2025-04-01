import geopandas as gpd
import polars as pl
from polarspiper import PolarsPiper


def move_null_columns_back(df: pl.DataFrame) -> pl.DataFrame:
    return df.select(
        df.null_count()
        .transpose(include_header=True)
        .sort("column_0")
        .select("column")
        .to_series()
        .to_list()
    )


def geometry_pairs_to_list_of_lat_lng(df: pl.DataFrame) -> pl.DataFrame:
    # geometry_coordinates is of type "(lat lng, lat lng, ....)"
    # We want to convert it into a list of tuples of floats.
    df = df.with_columns(
        pl.col("geometry_coordinates")
        .str.replace_all(r"\(", "")
        .str.replace_all(r"\)", "")
        .str.replace_all(", ", ";")
        .str.split(";")
    ).with_columns(
        geometry_coordinates=pl.col("geometry_coordinates").map_elements(
            lambda list_of_lists: [
                [float(_.split(" ")[1]), float(_.split(" ")[0])]
                for _ in list_of_lists
            ],
            return_dtype=list[list[float]],  # type: ignore
        )
    )
    return df


def get_roads(file: str) -> pl.DataFrame:
    df = (
        pl.read_csv(file, infer_schema_length=10_000)
        .pipe(PolarsPiper.drop_columns_that_are_all_null)
        .with_columns(
            geometry_type=pl.col("geometry").str.split(" ").list.first(),
            geometry_coordinates=pl.col("geometry")
            .str.split(" ")
            .list.slice(1)
            .list.join(" "),
        )
        .filter(pl.col("geometry_type") != "POLYGON")
        .pipe(geometry_pairs_to_list_of_lat_lng)
        .pipe(move_null_columns_back)
    )

    while True:  # loop until now more dead ends are removed
        prev_height = df.height

        endpoints = (
            df.filter(pl.col("geometry_type") == "LINESTRING")
            .select("id", "geometry_coordinates")
            .with_columns(
                start=pl.col("geometry_coordinates").list.first(),
                stop=pl.col("geometry_coordinates").list.last(),
            )
            .drop("geometry_coordinates")
        )

        point_count = (
            df.filter(pl.col("geometry_type") == "LINESTRING")
            .select("id", "geometry_coordinates")
            .explode("geometry_coordinates")
            .group_by("geometry_coordinates")
            .len()
        )

        start_is_okay = endpoints.join(
            point_count,
            left_on="start",
            right_on="geometry_coordinates",
            how="left",
        ).filter(pl.col("len") > 1)

        stop_is_okay = endpoints.join(
            point_count,
            left_on="stop",
            right_on="geometry_coordinates",
            how="left",
        ).filter(pl.col("len") > 1)

        valid_ids = (
            start_is_okay.join(stop_is_okay, on="id", how="inner")
            .filter((pl.col("len") > 1) & (pl.col("len_right") > 1))
            .select("id")
        )

        df = valid_ids.join(df, on="id", how="left")

        if df.height == prev_height:
            break
    return df


def get_points_of_interest(file: str, roads: pl.DataFrame) -> pl.DataFrame:
    return (
        (roads.explode("geometry_coordinates").select("geometry_coordinates"))
        .join(
            (
                pl.read_csv(file, infer_schema_length=10_000)
                .pipe(PolarsPiper.drop_columns_that_are_all_null)
                .with_columns(
                    geometry_type=pl.col("geometry")
                    .str.split(" ")
                    .list.first(),
                    geometry_coordinates=pl.col("geometry")
                    .str.split(" ")
                    .list.slice(1)
                    .list.join(" "),
                )
                .filter(pl.col("geometry_type") == "POINT")
                .pipe(geometry_pairs_to_list_of_lat_lng)
                .pipe(move_null_columns_back)
                .with_columns(pl.col("geometry_coordinates").list.first())
            ),
            on="geometry_coordinates",
            how="inner",
        )
        .pipe(move_null_columns_back)
    )


if __name__ == "__main__":
    gpd.read_file("data/raw/export-2.geojson").to_csv("data/raw/export-2.csv")
    df_roads = get_roads("data/raw/export-2.csv")
    df_poi = get_points_of_interest("data/raw/export-2.csv", df_roads)

    df_roads.write_parquet("data/processed/roads.parquet")
    df_poi.write_parquet("data/processed/points_of_interest.parquet")
