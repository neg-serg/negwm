def x4(self, mode: int) -> None:
    """ Move window to the 1,2,3,4 quad of 2D screen space
        mode (1,2,3,4): defines 1,2,3 or 4 quad of
                        screen space to move.
    """
    try:
        mode = int(mode)
    except TypeError:
        logging.error("cannot convert mode={mode} to int")
        return
    curr_scr = self.current_resolution
    self.current_win = self.i3ipc.get_tree().find_focused()
    if self.quad_use_gaps:
        gaps = self.useless_gaps
    else:
        gaps = {"w": 0, "a": 0, "s": 0, "d": 0}
    half_width = int(curr_scr['width'] / 2)
    half_height = int(curr_scr['height'] / 2)
    double_dgaps = int(gaps['d'] * 2)
    double_sgaps = int(gaps['s'] * 2)
    if mode == 1:
        geom = {
            'x': gaps['a'],
            'y': gaps['w'],
            'width': half_width - double_dgaps,
            'height': half_height - double_sgaps,
        }
    elif mode == 2:
        geom = {
            'x': half_width + gaps['a'],
            'y': gaps['w'],
            'width': half_width - double_dgaps,
            'height': half_height - double_sgaps,
        }
    elif mode == 3:
        geom = {
            'x': gaps['a'],
            'y': gaps['w'] + half_height,
            'width': half_width - double_dgaps,
            'height': half_height - double_sgaps,
        }
    elif mode == 4:
        geom = {
            'x': gaps['a'] + half_width,
            'y': gaps['w'] + half_height,
            'width': half_width - double_dgaps,
            'height': half_height - double_sgaps,
        }
    else:
        return
    if self.current_win is not None:
        if not self.geom_list[-1]:
            self.get_prev_geom()
        elif self.geom_list[-1]:
            prev = self.geom_list[-1].get('id', {})
            if prev != self.current_win.id:
                geom = self.get_prev_geom()

        actions.set_geom(self.current_win, geom)
