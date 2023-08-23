""" Properties lib to manipulate properties """
from typing import Set, Dict

class props:
    @staticmethod
    def pname(prop):
        if prop == 'title': return 'name'
        else: return prop

    @staticmethod
    def cfg_regex_props() -> Set[str]:
        """ Props with regexes """
        return {"class_r", "instance_r", "name_r", "role_r"}

    @staticmethod
    def cfg_props() -> Set[str]:
        """ Basic cfg properties, without regexes """
        return {'classw', 'instance', 'name', 'role'}

    @staticmethod
    def subtag_attr_list() -> Set[str]:
        """ Helper to create subtag attr list. """
        return {'class', 'instance', 'window_role', 'title'}

    @staticmethod
    def del_direct_props(config, win_attrs, target_tag: str) -> None:
        """ Remove basic(non-regex) properties of window from target tag.
            tag (str): target tag """
        for prop in config[target_tag].copy():
            if prop in props.cfg_props():
                if isinstance(config[target_tag][prop], str):
                    del config[target_tag][prop]
                elif isinstance(config[target_tag][prop], set):
                    for tok in config[target_tag][prop].copy():
                        if win_attrs[prop] == tok:
                            config[target_tag][prop].remove(tok)

    @staticmethod
    def del_regex_props(config, tree, win_attrs, target_tag: str) -> None:
        """ Remove regex properties of window from target tag.
            target_tag (str): target tag """
        def check_for_win_attrs(win, prop):
            class_r_check=(prop == "class_r" and winattr == win.window_class)
            instance_r_check=(prop == "instance_r" and winattr == win.window_instance)
            role_r_check=(prop == "role_r" and winattr == win.window_role)
            if class_r_check or instance_r_check or role_r_check:
                config[target_tag][prop].remove(target_tag)
        lst_by_reg=[]
        # Delete appropriate regexes
        for prop in config[target_tag].copy():
            if prop in props.cfg_regex_props():
                for reg in config[target_tag][prop].copy():
                    match prop:
                        case 'class_r': lst_by_reg=tree.find_classed(reg)
                        case 'instance_r': lst_by_reg=tree.find_instanced(reg)
                        case 'role_r': lst_by_reg=tree.find_by_role(reg)
                    winattr=win_attrs[prop[:-2]]
                    for win in lst_by_reg: check_for_win_attrs(win, prop)


    @staticmethod
    def str_to_winattr(win_attrs: Dict, prop_str: str) -> None:
        """ Parse property string to create win_attrs dict.
            prop_str (str): property string in special format. """
        prop_str=prop_str[1:-1]
        for token in prop_str.split('@'):
            if token:
                toks=token.split('=')
                attr, value=toks[0], toks[1]
                if value[0] == value[-1] and value[0] in {'"', "'"}:
                    value=value[1:-1]
                if attr in props.subtag_attr_list():
                    win_attrs[props.pname(attr)]=value
