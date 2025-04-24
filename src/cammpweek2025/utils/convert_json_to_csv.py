import glob
import os

import pandas as pd

# This script is only for Thomas and converts data into a more manageable format.


def main():
    files = glob.glob("data/workouts/*.json")
    df_list = []
    for file in files:
        df = pd.read_json(file).drop("cad", axis=1, inplace=False)
        blocks = []
        duration = 0
        power = None
        for _, row in df.iterrows():
            if power is None:
                duration = 1
                power = row["watts"]
            elif row["watts"] != power:
                blocks.append({"duration": duration + 1, "power": power})
                power = row["watts"]
                duration = 0
            else:
                duration += 1
        df_list.append(
            pd.DataFrame(blocks)
            .assign(
                workout_name=os.path.basename(file)
                .split("___")[0]
                .replace("_", " ")
            )
            .round({"power": 0})
            .astype({"power": "int"})
        )

    pd.concat(df_list, ignore_index=True).to_csv(
        "data/workouts.csv", index=False
    )


if __name__ == "__main__":
    main()
