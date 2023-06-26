import pandas as pd


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
