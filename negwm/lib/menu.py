""" Menu helper library """
from typing import List

class menu():
    @staticmethod
    def args(P: dict, prompt='❯>', matching='fuzzy') -> List[str]:
        """ Create run parameters to spawn menu process from dict
            P(dict): parameters for menu
            List(str) to do menu subprocessing """
        return [
            'rofi', 
            '-show',
            '-dmenu',
            '-disable-history',
            P.get('auto-select', '-no-auto-select'),
            P.get('markup_rows', '-no-markup-rows'),
            P.get('matching', '-no-markup-rows'),
            '-p', P.get('prompt', prompt),
            '-i',
            '-matching', f'{matching}'
        ]

    @staticmethod
    def wrap_str(s: str, lfs='⟬', rhs='⟭') -> str:
        """ String wrapper to make it beautiful """
        return f'{lfs}{s}{rhs}'
