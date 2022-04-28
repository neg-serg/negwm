from typing import List
from . extension import extension
from . misc import Misc

class Rules():
    @staticmethod
    def fill_rules_dict(mod, cmd_dict) -> List:
        config = mod.cfg
        for tag in config:
            cmd_dict[tag] = []
            for attr in config[tag]:
                for fill in ['classw', 'instance', 'name', 'role']:
                    cmd_dict[tag].append(Rules.info(config, tag, attr, fill))
        return cmd_dict

    @staticmethod
    def rules_mod(modname):
        """ Create i3 match rules for all tags. """
        ret = ''
        mods = extension.get_mods()
        if mods is None or not mods:
            return ret
        mod = mods.get(modname, None)
        if mod is None:
            return ''
        cmd_dict = Rules.fill_rules_dict(mod, {})
        for tag in cmd_dict:
            rules = list(filter(lambda str: str != '', cmd_dict[tag]))
            if rules:
                ret += f'set ${modname}-{tag} [' + ' '.join(rules) + ']\n'
        return ret + mod.rules(cmd_dict)

    @staticmethod
    def info(config: dict, tag: str, attr: str, fill: str) -> str:
        """ Create rule in i3 commands format
            config (dict): extension config.
            tag (str): target tag.
            attr (str): tag attrubutes.
            fill (str): attribute to fill. """
        conv_dict_attr = {
            'classw': 'class',
            'instance': 'instance',
            'name': 'window_name',
            'role': 'window_role'
        }
        cmd = ''
        if fill in attr:
            if not attr.endswith('_r'):
                win_attr = conv_dict_attr[attr]
            else:
                win_attr = conv_dict_attr[attr[:-2]]
            start = f'{win_attr}="' + Misc.ch(config[tag][attr], '^')
            attrlist = []
            attrlist = config[tag][attr]
            if config[tag].get(attr + '_r', ''):
                attrlist += config[tag][attr + '_r']
            if not attr.endswith('_r'):
                cmd = start + Misc.parse_attr(attrlist, end='')
            if cmd:
                cmd += '"'
        return cmd
