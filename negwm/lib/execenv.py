import os
from os.path import expanduser
import errno
import shutil
import threading
import multiprocessing
import logging


class utils():
    @staticmethod
    def xdg_config_home() -> str: return os.environ.get('XDG_CONFIG_HOME', '')

    @staticmethod
    def run_once(f):
        def wrapper(*args, **kwargs):
            if not wrapper.has_run:
                wrapper.has_run = True
                return f(*args, **kwargs)
        wrapper.has_run = False
        return wrapper

    @staticmethod
    def cache_path() -> str:
        ''' Easy way to return negwm cache path. '''
        cachedir_env=os.environ.get('NEGWM_CACHE', '')
        cache_home=os.environ.get('XDG_CACHE_HOME', '')
        if cachedir_env:
            utils.create_dir(cachedir_env)
            return cachedir_env
        elif cache_home:
            utils.create_dir(f'{cache_home}/negwm')
            return f'{cache_home}/negwm'
        else:
            home=os.environ.get('HOME', '')
            if not home:
                logging.error(f'Fatal! HOME env is not set')
                return ''
            else:
                default_cfg_dir=f'{home}/.cache/negwm'
                utils.create_dir(default_cfg_dir)
                return default_cfg_dir

    @staticmethod
    def create_dir(dirname) -> None:
        ''' Helper function to create directory
            dirname(str): directory name to create '''
        if os.path.isdir(dirname):
            return
        try:
            logging.info(f'Creating dir {dirname}')
            os.makedirs(dirname)
        except OSError as oserr:
            if oserr.errno != errno.EEXIST:
                raise

class execenv():
    ''' Environment class. It is a helper for tmux manager to store info about currently selected application. This class rules over
    parameters and settings of application, like used terminal enumator, fonts, all path settings, etc.
    config: manager to autosave/autoload configutation with inotify '''
    cache = utils.cache_path()
    paths = {}

    def __init__(self, name: str, config) -> None:
        self.name, self.config = name, config
        if not self.cfg_block():
            logging.error(f'Cannot create config for {name}, with config {config}')
            return
        utils.create_dir(utils.cache_path())
        blk = self.cfg_block()
        term = self.term()
        blk.setdefault('exec', [])
        blk.setdefault('exec_tmux', [])
        blk.setdefault('exec_dtach', [])
        self.exec_tmux = blk['exec_tmux']
        if not self.exec_tmux:
            exec_dtach = blk['exec_dtach']
            if not exec_dtach:
                self.exec = blk['exec']
            else:
                execenv.prepare_dtach()
                self.exec = f'dtach -A {execenv.paths["dtach_session_dir"]}' \
                            f'/{name}.session {exec_dtach}'
        blk.setdefault('classw', term)
        self.wclass = blk['classw']
        self.opts = getattr(self, term)()

        def join_processes():
            for prc in multiprocessing.active_children():
                prc.join()
        threading.Thread(target=join_processes, args=(), daemon=True).start()

    @utils.run_once
    @staticmethod
    def prepare_alacritty():
        execenv.paths['alacritty_cfg_dir'] = f'{execenv.cache}/alacritty_cfg'
        execenv.paths['alacritty_cfg'] = expanduser(f'{utils.xdg_config_home()}/alacritty/alacritty.yml')
        utils.create_dir(execenv.paths['alacritty_cfg_dir'])

    @utils.run_once
    @staticmethod
    def prepare_tmux():
        execenv.paths['tmux_socket_dir'] = f'{execenv.cache}/tmux_sockets'
        utils.create_dir(execenv.paths['tmux_socket_dir'])

    @utils.run_once
    @staticmethod
    def prepare_dtach():
        execenv.paths['dtach_session_dir'] = f'{execenv.cache}/dtach_sessions'
        utils.create_dir(execenv.paths['dtach_session_dir'])

    @staticmethod
    def tmux_socket_path(name):
        return expanduser(f'{execenv.paths["tmux_socket_dir"]}/{name}.socket')

    @staticmethod
    def tmux_session_attach(name):
        return f'tmux -S {execenv.tmux_socket_path(name)} a -t {name}'

    @staticmethod
    def tmux_new_session(name):
        return f'tmux -S {execenv.tmux_socket_path(name)} new-session -s {name}'

    def cfg_block(self) -> dict:
        return self.config.get(self.name, {})

    def shell(self) -> str:
        return self.cfg_block().get('shell', 'dash')

    def font(self) -> str:
        ret = self.config.get('default_font', '')
        if not ret:
            ret = self.cfg_block().get('font', 'Iosevka')
        return ret

    def font_size(self) -> str:
        return self.cfg_block().get('font_size', '14')

    def term(self):
        term = self.cfg_block().get('term', '')
        if term:
            return term
        # Detect fallback terminal
        for t in ['alacritty', 'kitty', 'st', 'zutty']:
            if shutil.which(t):
                return t
        logging.error('No supported terminal installed, fail :(')
        return ''

    def style(self) -> dict:
        use_one_fontstyle = self.config.get('use_one_fontstyle', False)
        style = self.config.get('default_style', '')
        if not style:
            style = self.cfg_block().get('style', 'Regular')
        if use_one_fontstyle:
            return {
                'normal': self.cfg_block().get('font_normal', style),
                'bold' : self.cfg_block().get('font_bold', style),
                'italic': self.cfg_block().get('font_italic', style)
            }
        else:
            return {
                'normal': self.cfg_block().get('font_normal', 'Regular'),
                'bold' : self.cfg_block().get('font_bold', 'Bold'),
                'italic': self.cfg_block().get('font_italic', 'Italic')
            }

    def alacritty(self) -> str:
        execenv.prepare_alacritty()

        def create_alacritty_cfg(name: str) -> str:
            ''' Config generator for alacritty. We need it because of alacritty
            cannot bypass most of user parameters with command line now.
            cfg_dir: alacritty config dir
            config: config dirtionary
            name(str): name of config to generate
            cfgname(str): configname '''
            app_name = self.config.get(name, {}).get('app_name', '')
            if not app_name:
                app_name = self.config.get(name, {}).get('classw')
            app_name = f'{app_name}.yml'
            cfgname = expanduser(f'{execenv.paths["alacritty_cfg_dir"]}/{app_name}')
            shutil.copyfile(execenv.paths["alacritty_cfg"], cfgname)
            return cfgname

        def alacritty_yml_create(custom_config: str) -> None:
            ''' Create config for alacritty
            custom_config(str): config name to create '''
            import yaml
            import yamlloader
            conf = None
            with open(custom_config, 'r', encoding='utf-8') as cfg_file:
                try:
                    conf = yaml.load(
                        cfg_file, Loader=yamlloader.ordereddict.CSafeLoader)
                    if conf is not None:
                        if 'font' in conf:
                            font = conf['font']
                            for w in 'normal', 'bold', 'italic':
                                font[w]['family'] = self.font()
                                font[w]['style'] = self.style()[w]
                            font['size'] = self.font_size()
                        if 'window' in conf:
                            window = conf['window']
                            padding = self.cfg_block().get('padding', [2, 2])
                            opacity = self.cfg_block().get('opacity', 0.88)
                            window['opacity'] = opacity
                            window['padding']['x'] = int(padding[0])
                            window['padding']['y'] = int(padding[1])
                except yaml.YAMLError as yamlerror:
                    logging.error(yamlerror)

            if conf is not None and conf:
                with open(custom_config, 'w', encoding='utf8') as outfile:
                    try:
                        yaml.dump(
                            conf,
                            outfile,
                            default_flow_style=False,
                            allow_unicode=True,
                            canonical=False,
                            explicit_start=True,
                            Dumper=yamlloader.ordereddict.CDumper
                        )
                    except yaml.YAMLError as yamlerror:
                        logging.error(yamlerror)

        self.title = self.cfg_block().get('title', self.wclass)
        custom_config = create_alacritty_cfg(self.name)
        multiprocessing.Process(
            target=alacritty_yml_create, args=(custom_config,),
            daemon=True
        ).start()

        return ' '.join([
            f'{self.term()}',
            f'--config-file {expanduser(custom_config)}',
            f'--class {self.wclass},{self.wclass}',
            f'-t {self.title} -e'])

    def st(self):
        return ' '.join([
            f'{self.term()}',
            f'-c {self.wclass}',
            f'-t {self.name}',
            f"-f {self.font} :size={str(self.font_size())}:style={self.style()['normal']}",
            '-e'])

    def kitty(self):
        cfg = self.cfg_block()
        padding = cfg.get('padding', [0, 0])[0]
        opacity = cfg.get('opacity', 0.88)
        instance_group = cfg.get('instance_group', self.name)
        style = self.style()['normal']
        if style == 'Regular':
            style=''
        else:
            style=f' {style}'
        font_settings=[
            f'-o font_family=\'{self.font()}{style}\'',
            f'-o font_size={str(self.font_size())}'
        ]
        return ' '.join([
            f'{self.term()}',
            '-1', f'--instance-group {instance_group}',
            f'--class={self.wclass}',
            f'--title={self.name}',
            f'-o window_padding_width={padding}',
            f'-o background_opacity={opacity}'] + font_settings)

    def zutty(self):
        return ' '.join([
            f'{self.term()}',
            f'-name {self.wclass}',
            f'-font {self.font}',
            f'-fontsize {str(self.font_size())}'])
