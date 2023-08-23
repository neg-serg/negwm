""" All extensions cat send messages :) """
from typing import List
from typing import Dict
from negwm.lib.msgbroker import MsgBroker

class extension():
    def __init__(self):
        pass

    @staticmethod
    def get_mods() -> Dict:
        return MsgBroker.get_mods()

    @staticmethod
    def get_mods_list() -> List:
        return list(MsgBroker.get_mods_list())

    def send_msg(self, args: List):
        """ Creates bindings from socket IPC to current module public function
        calls. This function defines bindings to the module methods that can be
        used by external users as i3-bindings, etc. Need the [send] binary
        which can send commands to the appropriate socket.
        args (List): argument list for the selected function. """
        return getattr(self, args[0])(*args[1:])
