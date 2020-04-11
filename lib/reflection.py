""" Static functions for negi3wm reflection """
from lib.msgbroker import MsgBroker

class Reflection():
    """ Implements various reflection functions """
    @staticmethod
    def get_mods():
        return MsgBroker.get_mods()
