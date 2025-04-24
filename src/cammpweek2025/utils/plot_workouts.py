import matplotlib.pyplot as plt
import pandas as pd


def main():
    plt.close("all")
    df = pd.read_csv("data/workouts.csv")
    n = df["workout_name"].nunique()
    fig, axs = plt.subplots(n, 1, figsize=(6, 3 * n))
    fig.subplots_adjust(hspace=0.5)
    for i, (group, dfgroup) in enumerate(df.groupby("workout_name")):
        edges = dfgroup["duration"].cumsum().to_list()
        edges = [0] + edges
        values = dfgroup["power"].to_list()

        axs[i].stairs(edges=edges, values=values)
        axs[i].set(
            title=group,
            xlabel="Time (s)",
            ylabel="Power (W)",
            xlim=(0, edges[-1] + 10),
            ylim=(-10, dfgroup["power"].max() + 100),
        )
        axs[i].grid()
    plt.show()


if __name__ == "__main__":
    main()
