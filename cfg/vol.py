from enum import Enum

class Vol(Enum):
    mpd_addr = '::1'
    mpd_buf_size = 1024
    mpd_inc = 1
    mpd_port = '6600'
    mpv_socket = '/tmp/mpv.socket'
    use_mpv09 = 1
