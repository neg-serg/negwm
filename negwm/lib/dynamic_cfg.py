from negwm.lib.cfg import cfg
from negwm.lib.props import props

class dynamic_cfg(cfg):
    def __init__(self, i3) -> None:
        super().__init__(i3)
        self.win_attrs={}                   # used for props add / del hacks
        self.additional_props=[dict()]      # used to store add_prop history
        if not self.cfg: self.cfg={}

    def add_props(self, tag: str, prop_str: str) -> None:
        """ Move window to some tag.
            tag (str): target tag
            prop_str (str): property string in special format. """
        config=self.cfg
        props.str_to_winattr(self.win_attrs, prop_str)
        factors=props.cfg_props() & set(self.win_attrs.keys())
        if not tag in config:
            return
        tagcfg=config[tag]
        for tok in factors:
            if self.win_attrs[tok] not in tagcfg.get(tok, {}):
                if tok in tagcfg:
                    if isinstance(tagcfg[tok], str):
                        tagcfg[tok]={self.win_attrs[tok]}
                    elif isinstance(tagcfg[tok], list):
                        tagcfg[tok].append(self.win_attrs[tok])
                        tagcfg[tok]=list(dict.fromkeys(tagcfg[tok]))
                else:
                    tagcfg.update({tok: self.win_attrs[tok]})
                # fix for the case where attr is just attr not {attr}
                if isinstance(self.conf(tag, tok), str):
                    tagcfg[tok]={self.win_attrs[tok]}
        self.additional_props.append({
            'mod': self.__class__.__name__,
            'tag': tag,
            'prop': prop_str})
        self.additional_props=list(filter(len, self.additional_props))

    def del_props(self, tag: str, prop_str: str) -> None:
        """ Remove window from some tag.
        tag (str): target tag
        prop_str (str): property string in special format. """
        config=self.cfg
        tree=self.i3ipc.get_tree()
        props.str_to_winattr(self.win_attrs, prop_str)
        props.del_direct_props(config, self.win_attrs, tag)
        props.del_regex_props(config, tree, self.win_attrs, tag)
        for prop in props.cfg_regex_props() | props.cfg_props():
            if prop in self.conf(tag) and self.conf(tag, prop) == set():
                del config[tag][prop]
