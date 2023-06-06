import requests
from typing import Literal, Optional


MethodLiteral = Literal["GET", "POST"]
ModalityLiteral = Literal["speed", "smoothness", "rotation", "proxemics"]


class Modality(object):
    def __init__(
        self,
        name: ModalityLiteral,
        base_url: str,
        increase_path: str,
        increase_method: Optional[MethodLiteral],
        decrease_path: str,
        decrease_method: Optional[MethodLiteral],
        neutral_path: str,
        neutral_method: Optional[MethodLiteral],
        **kwargs
    ):
        self.name = name
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

    def _post(url: str, body: Optional[dict]):
        response = requests.post(url, json=body)
        return response.json()

    def increase(self, body: Optional[dict]):
        if self.increase_method == "POST":
            return self._post(self.base_url + self.increase_path, body)
        else:
            # GET
            return self._get(self.base_url + self.increase_path)

    def decrease(self, body: Optional[dict]):
        if self.decrease_method == "POST":
            return self._post(self.base_url + self.decrease_path, body)
        else:
            # GET
            return self._get(self.base_url + self.decrease_path)

    def neutral(self, body: Optional[dict]):
        if self.neutral_path is None:
            return None
        if self.neutral_method == "POST":
            return self._post(self.base_url + self.neutral_path, body)
        else:
            # GET
            return self._get(self.base_url + self.neutral_path)
