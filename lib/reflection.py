""" Static functions for negwm reflection """
from typing import Dict
from msgbroker import MsgBroker

class Reflection():
    """ Implements various reflection functions """
    @staticmethod
    def get_mods() -> Dict:
        return MsgBroker.get_mods()
