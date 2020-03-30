from typing import List


class extension():
    def __init__(self):
        self.bindings = {}

    def send_msg(self, args: List) -> None:
        """ Creates bindings from socket IPC to current module public function
            calls.

            This function defines bindings to the module methods that
            can be used by external users as i3-bindings, sxhkd, etc. Need the
            [send] binary which can send commands to the appropriate socket.

            Args:
                args (List): argument list for the selected function.
        """
        self.bindings[args[0]](*args[1:])
