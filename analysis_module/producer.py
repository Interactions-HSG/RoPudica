import pandas as pd
import warnings

from datetime import datetime, timedelta
from trend_classifier import Segmenter
from typing import Callable
from types import FunctionType as function
from modality import ModalityLiteral

AVAILABLE_HANDLER = {"_handle_trend"}


class Producer(object):
    def __init__(
        self,
        subscription_topic: str,
        analysis_interval: int,
        threshold: float,
        handler: str | function,
        output_modalities: dict[ModalityLiteral, float],
        **kwargs,
    ):
        if len(output_modalities) == 0:
            raise ValueError("At least one output modality must be specified")
        self.subscription_topic = subscription_topic
        self._data = pd.DataFrame(
            columns=["value"], index=pd.DatetimeIndex(name="timestamp", data=[])
        )
        self._analysis_interval = analysis_interval
        self._threshold = threshold
        self._handler = Producer.match_function(handler)
        self._modalities = output_modalities

    @staticmethod
    def match_function(handler: str | function):
        if type(handler) is function:
            return handler
        elif type(handler) is str and handler in AVAILABLE_HANDLER:
            return getattr(Producer, handler)
        else:
            raise TypeError(
                "Handler must be a function or an existing handler method of Producer"
            )

    def add_data(self, data: dict):
        new_df = pd.DataFrame.from_dict([data])
        new_df.set_index(
            pd.DatetimeIndex(data=new_df["timestamp"], name="timestamp"), inplace=True
        )
        new_df.drop(columns=["timestamp", "id"], inplace=True)

        temp_df = pd.concat([self._data, new_df])
        self._data = temp_df.last(pd.Timedelta(seconds=self._analysis_interval))

    def handle(self):
        value = self._handler(self._data, self._threshold)
        output = {}
        for modality, weight in self._modalities.items():
            output[modality] = value * weight if value else 0

        return output

    @staticmethod
    def _handle_trend(df: pd.DataFrame, threshold: float):
        df_length = len(df.index.tolist())

        if df_length < 2:
            return 0

        x_in = list(range(0, df_length, 1))
        y_in = df["value"].tolist()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            seg = Segmenter(x_in, y_in, n=df_length)
            segments = seg.calculate_segments()

        slope = segments[0].slope
        if slope > (5 * threshold) or slope < (-5 * threshold):
            return 0
        print(f"Current slope: {slope}, threshold: {threshold}", flush=True)
        if slope > threshold:
            return 1
        elif slope < -threshold:
            return -1
        else:
            return 0
