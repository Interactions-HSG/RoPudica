import pandas as pd
from scipy.signal import find_peaks


def handle_expression(df: pd.DataFrame, threshold: float):
    emotions = {
        "angry": -1,
        "fear": -1,
        "neutral": 0,
        "sad": -1,
        "disgust": -1,
        "happy": 1,
        "surprise": -1,
    }

    running_sum = 0
    for expression in df["value"].tolist():
        running_sum += emotions[expression]

    if running_sum < threshold:
        return 1
    else:
        return 0


def find_spikes(df: pd.DataFrame, threshold: float):
    values = df["value"].to_numpy()
    # find positive and negative peaks
    pos_peaks, _ = find_peaks(values, distance=2, threshold=threshold)
    neg_peaks, _ = find_peaks(-values, distance=2, threshold=threshold)

    pos_len = len(pos_peaks)
    neg_len = len(neg_peaks)
    if pos_len > 0 and neg_len > 0:
        return 0
    elif pos_len > 0:
        print("positive spike", flush=True)
        return 1
    elif neg_len > 0:
        print("negative spike", flush=True)
        return -1
    return 0
