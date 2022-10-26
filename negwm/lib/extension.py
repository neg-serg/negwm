from typing import List
from negwm.lib.reflection import Reflection

class extension():
    def __init__(self):
        pass

    @staticmethod
    def get_mods():
        return Reflection.get_mods()

    def send_msg(self, args: List):
        """ Creates bindings from socket IPC to current module public function
        calls. This function defines bindings to the module methods that can be
        used by external users as i3-bindings, etc. Need the [send] binary
        which can send commands to the appropriate socket.
        args (List): argument list for the selected function. """
        return getattr(self, args[0])(*args[1:])
