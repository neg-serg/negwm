""" Create a pid lock with abstract socket.
    Taken from [https://stackoverflow.com/questions/788411/check-to-see-if-python-script-is-running]
"""

import sys
import socket
import logging

def get_lock(process_name: str, verbose=False) -> None:
    """
    Without holding a reference to our socket somewhere it gets garbage
    collected when the function exits
    process_name (str): process name to bind. """
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        get_lock._lock_socket.bind('\0' + process_name)
        if verbose:
            logging.info('locking successful')
    except socket.error:
        logging.error('lock exists')
        sys.exit()
