import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

X = pd.Series(np.arange(50))


def main():
    # trend_line()
    # spike()
    # states()
    complete()
    pass


def save_plot(y, x=X):
    data = pd.DataFrame(index=x, data={"data": y})
    return data.plot()


def trend_line():
    y = pd.Series(10 + (0.2 * X + np.random.randint(-3, +3, 50)))
    save_plot(y)
    plt.savefig("trend.png", bbox_inches="tight")


def spike():
    y = pd.Series(30 + (np.random.randint(-5, +5, 50)))
    y[19] = 41
    y[20] = 50
    y[21] = 48
    y[22] = 47
    y[23] = 44

    save_plot(y)
    plt.savefig("spike.png", bbox_inches="tight")


def states():
    emotion_mapping = {
        0: "angry",
        1: "fear",
        2: "sad",
        3: "neutral",
        4: "disgust",
        5: "happy",
        6: "surprise",
    }
    random_values = np.random.randint(0, 6, 10)
    data = np.repeat(random_values, 5)
    y = pd.Series(data)

    ax = save_plot(y)
    ax.set_yticklabels(emotion_mapping.values())
    plt.savefig("states.png", bbox_inches="tight")


def annotate(ax, index, weight, threshold, slope=None):
    annotations = [f"$p_{index}$", f"weight: ${weight}$", f"threshold: ${threshold}$"]
    if slope:
        annotations.append(f"slope: ${slope}$")

    for i, annotation in enumerate(annotations):
        ax.annotate(
            annotation,
            xy=(1.05, 0.6 - i * 0.15),
            xycoords="axes fraction",
            fontstyle="normal" if i == 0 else "italic",
        )


def complete():
    t = np.arange(-5.0, 0, 0.01)

    # plt.figure().set_figwidth(200)

    # p1
    s1 = 7 + 0.1 * np.random.random(len(t))
    s1[: int(len(s1) * 0.3) + 1] = 0
    ax1 = plt.subplot(311)
    plt.plot(t, s1)
    plt.ylim(6, 8)
    plt.axvline(x=-3.5, color="k", linewidth=2.5)
    plt.axvline(x=0, color="k", linewidth=5)
    plt.tick_params("x", labelsize=6)
    plt.tick_params("x", labelbottom=False)  # make these tick labels invisible
    ax1.set_yticklabels(["", 6.5, 7.0, 7.5, ""])
    annotate(ax1, 1, 0.2, 0.05, 0.01)

    # p2
    slope = 0.7
    random_values = 2 + 1.2 * np.random.random(len(t))
    random_values.sort()
    linear_slope_values = slope * random_values
    linear_slope_values[: int(len(linear_slope_values) * 0.2) + 1] = 0
    ax2 = plt.subplot(312, sharex=ax1)
    plt.plot(t, linear_slope_values)
    plt.ylim(1.5, 2.5)
    plt.axvline(x=-4, color="k", linewidth=2.5)
    plt.axvline(x=0, color="k", linewidth=5)
    plt.tick_params("x", labelsize=6)
    plt.tick_params("x", labelbottom=False)  # make these tick labels invisible
    ax2.set_yticklabels(["", 1.5, 2.0, 2.5, ""])
    annotate(ax2, 2, 0.5, 0.2, 0.35)

    # p3
    s3 = 1.3 + 0.8 * np.random.random(len(t))
    s3[int(len(s3) * 0.93) : int(len(s3) * 0.96)] += 1.47
    s3[: int(len(s3) * 0.8) + 1] = 0
    ax3 = plt.subplot(313, sharex=ax1)
    plt.plot(t, s3)
    plt.ylim(1, 5)
    plt.axvline(x=-1, color="k", linewidth=2.5)
    plt.axvline(x=0, color="k", linewidth=5)
    ax3.set_yticklabels(["", 2, 3, 4, ""])
    annotate(ax3, 3, 0.3, 0.7)

    plt.xlim(-5, 0)
    plt.subplots_adjust(hspace=0.0)
    plt.xlabel("seconds (s) until $t_0$")
    plt.show()


if __name__ == "__main__":
    main()
