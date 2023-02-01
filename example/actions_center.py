def center_geom(self, win, change_geom: bool = False, degrade_coeff: float = 0.82):
    """ Move window to the center with geometry optional changing.
    win: target window.
    change_geom (bool): predicate to change geom to the [degrade_coeff]
    of the screen space in both dimenhions.
    degrade_coeff (int): coefficient which denotes change geom of the
    target window. """
    geom, center = {}, {}
    if degrade_coeff > 1.0:
        degrade_coeff = 1.0
    center['x'] = int(self.current_resolution['width'] / 2)
    center['y'] = int(self.current_resolution['height'] / 2)
    if not change_geom:
        geom['width'] = int(win.rect.width)
        geom['height'] = int(win.rect.height)
    else:
        geom['width'] = int(
            self.current_resolution['width'] * degrade_coeff
        )
        geom['height'] = int(
            self.current_resolution['height'] * degrade_coeff
        )
    geom['x'] = center['x'] - int(geom['width'] / 2)
    geom['y'] = center['y'] - int(geom['height'] / 2)
    return geom

def center(self, resize: str) -> None:
    """ Move window to center
    resize (str): predicate which shows resize target window or not. """
    focused = self.i3ipc.get_tree().find_focused()
    if resize in {"default", "none"}:
        geom = self.center_geom(focused)
        actions.set_geom(focused, geom)
    elif resize in {"resize", "on", "yes"}:
        geom = self.center_geom(focused, change_geom=True)
        actions.set_geom(focused, geom)
    else:
        return
