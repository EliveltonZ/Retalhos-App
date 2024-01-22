from abc import ABC, abstractmethod
from typing import Literal


class IEletronics(ABC):

    def __init__(self) -> None:
        self._volume = 10
        self._power = False

    def power(self, power: bool) -> Literal['ON', 'OFF']:
       self._power = power
       return 'ON' if self._power else 'OFF'

    @abstractmethod
    def increase_volume(self) -> None: pass

    @abstractmethod
    def decrease_volume(self) -> None: pass


class IControl(ABC):
    ...


lista = ['email, nome, sobrenome, idade, telefone, cidade']