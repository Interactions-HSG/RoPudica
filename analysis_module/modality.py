import requests
from typing import Literal, Optional


MethodLiteral = Literal["GET", "POST"]
ModalityLiteral = Literal["speed", "smoothness", "rotation", "proxemics"]


class Modality(object):
    def __init__(
        self,
        name: ModalityLiteral,
        threshold: float,
        base_url: str,
        increase_path: str,
        decrease_path: str,
        neutral_path: str = None,
        increase_method: MethodLiteral = "POST",
        decrease_method: MethodLiteral = "POST",
        neutral_method: MethodLiteral = "POST",
        **kwargs,
    ):
        self.name = name
        self.threshold = threshold
        self.base_url = base_url
        self.increase_path = increase_path
        self.increase_method = increase_method
        self.decrease_path = decrease_path
        self.decrease_method = decrease_method
        self.neutral_path = neutral_path
        self.neutral_method = neutral_method

    def _get(url: str):
        response = requests.get(url)
        return response.json()

    def _post(url: str, body: dict = None):
        response = requests.post(url, json=body) if body else requests.post(url)
        return response.json()

    def increase(self, body: dict = None):
        if self.increase_method == "POST":
            return self._post(self.base_url + self.increase_path, body)
        else:
            # GET
            return self._get(self.base_url + self.increase_path)

    def decrease(self, body: dict = None):
        if self.decrease_method == "POST":
            return self._post(self.base_url + self.decrease_path, body)
        else:
            # GET
            return self._get(self.base_url + self.decrease_path)

    def neutral(self, body: dict = None):
        if self.neutral_path is None:
            return None
        if self.neutral_method == "POST":
            return self._post(self.base_url + self.neutral_path, body)
        else:
            # GET
            return self._get(self.base_url + self.neutral_path)
