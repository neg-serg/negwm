from typing import List

class menu():
    @staticmethod
    def args(params: dict, prompt='❯>', matching='fuzzy') -> List[str]:
        """ Create run parameters to spawn rofi process from dict
            params(dict): parameters for rofi
            List(str) to do rofi subprocessing """
        params['prompt'] = params.get('prompt', prompt)
        params['markup_rows'] = params.get('markup_rows', '-no-markup-rows')
        params['auto-select'] = \
            params.get('auto-select', "-no-auto-select")
        return [
            'rofi', '-show', '-dmenu', '-disable-history',
            params['auto-select'], params['markup_rows'],
            '-p', params['prompt'], '-i', '-matching', f'{matching}']

    @staticmethod
    def wrap_str(s: str, lfs='⟬', rhs='⟭') -> str:
        """ String wrapper to make it beautiful """
        return f'{lfs}{s}{rhs}'
