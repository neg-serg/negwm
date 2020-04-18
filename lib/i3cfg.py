#!/usr/bin/python3

from cfg import cfg
from extension import extension
from misc import Misc
from typing import List
import textwrap

class i3cfg(extension, cfg):
    def __init__(self, i3) -> None:
        cfg.__init__(self, i3)
        # i3ipc connection, bypassed by negi3wm runner
        self.i3ipc = i3

        self.bindings = {
            "show": self.show_cfg,
            "write":self.write_cfg,
        }

        self.send_path = '${XDG_CONFIG_HOME}/i3/bin/send'

    def generate(self):
        ret = []
        cfg_sections = self.cfg.get('sections', [])
        if cfg_sections:
            for section in cfg_sections:
                section_data = getattr(self, section)()
                ret.append(textwrap.dedent(section_data))
        return ret

    def show_cfg(self) -> None:
        print(''.join(self.generate()))

    def write_cfg(self) -> None:
        i3_config = '/home/neg/.config/i3/_config'
        with open(i3_config, 'w', encoding='utf8') as outfile:
            outfile.write('\n'.join(self.generate()))

    def autostart(self) -> str:
        autostart_list = [
            "exec_always zsh -c ${XDG_CONFIG_HOME}/i3/bin/negi3wm_run &",
            "exec_always ${XDG_CONFIG_HOME}/i3/bin/gnome_settings &",
            "exec_always ${XDG_CONFIG_HOME}/i3/bin/panel_run.sh &",
            "exec /usr/lib/gsd-xsettings &",
            "exec /usr/sbin/gpaste-client daemon &",
        ]
        return '\n'.join(autostart_list) + '\n'

    def gaps(self) -> str:
        gaps = [0, 0, 0, 0]
        gaps_params = [
            f'gaps inner {gaps[0]}',
            f'gaps outer {gaps[1]}',
            f'gaps top {gaps[2]}',
            f'gaps bottom {gaps[3]}'
        ]
        return '\n'.join(gaps_params) + '\n'

    def general(self) -> str:
        return """
        workspace_layout tabbed
        floating_modifier Mod4

        set $i3 ${XDG_CONFIG_HOME}/i3

        set $exit mode "default"
        """

    def focus_settings(self) -> str:
        ret = """
        focus_follows_mouse no
        force_display_urgency_hint 0 ms
        focus_on_window_activation urgent
        focus_wrapping yes
        mouse_warping none
        """
        return ret

    def colorscheme(self) -> str:
        appearance = """
        show_marks yes
        smart_borders on
        hide_edge_borders both
        title_align left
        """

        theme = {
            'client.focused': [
                '#222233', '#000000', '#ddddee', '#112211', '#0C0C0D'
            ],
            'client.focused_inactive': [
                '#000000', '#000000', '#005fff', '#000000', '#222233'
            ],
            'client.unfocused': [
                '#000000', '#000000', '#315c70', '#000000', '#222233'
            ],
            'client.urgent': [
                '#000000', '#2E2457', '#4C407C', '#32275E', '#32275E'
            ],
            'client.placeholder': [
                '#000000', '#0c0c0c', '#ffffff', '#000000', '#0c0c0c'
            ],
            'client.background': ['#000000'],
        }
        colorscheme = ''
        for param, data in theme.items():
            colorscheme += f"{param} {' '.join(data)}\n"

        return textwrap.dedent(appearance) \
            + textwrap.dedent(colorscheme)

    def bscratch_bindings(self, mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p, subtag='') -> str:
            ret = ''
            pref, postfix = '', ''
            if mode != 'default':
                pref, postfix = '\t', ', $exit'
            get_binds = p.split('_')
            mode_ = get_binds[1]
            cmd = get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    for keybind in settings[p]:
                        ret += f'{pref.strip()} bindsym {keybind.strip()}' \
                            f' $bscratch {cmd.strip()} {tag.strip()} ' \
                            f'{subtag.strip()} {postfix.strip()}\n'
            return ret

        bscratch = extension.get_mods()['bscratch']
        for tag,settings in bscratch.cfg.items():
            for param in settings:
                if isinstance(settings[param], dict):
                    for p in settings[param]:
                        if p.startswith('keybind_'):
                            subtag = param
                            ret += get_binds(
                                mode, tag, settings[param], p, subtag=subtag
                            )
                elif param.startswith('keybind_'):
                    ret += get_binds(mode, tag, settings, param)
        return textwrap.dedent(ret)

    def circle_bindings(self, mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p, subtag='') -> str:
            ret = ''
            pref, postfix = '', ''
            if mode != 'default':
                pref, postfix = '\t', ', $exit'
            get_binds = p.split('_')
            mode_ = get_binds[1]
            cmd = get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    for keybind in settings[p]:
                        ret += f'{pref}bindsym {keybind} $circle' \
                            f' {cmd} {tag} {subtag} {postfix}\n'
            return textwrap.dedent(ret)

        circle = extension.get_mods()['circle']
        for tag, settings in circle.cfg.items():
            for param in settings:
                if isinstance(settings[param], dict):
                    for p in settings[param]:
                        if p.startswith('keybind_'):
                            subtag = param
                            ret += get_binds(
                                mode, tag, settings[subtag], p, subtag
                            )
                elif param.startswith('keybind_'):
                    ret += get_binds(mode, tag, settings, param)
        return textwrap.dedent(ret)

    def font(self) -> str:
        return "font pango: Iosevka Term Heavy 9"

    def mods_commands(self) -> str:
        ret = ''
        for mod in sorted(extension.get_mods()):
            ret += (f'set ${mod} exec --no-startup-id {self.send_path} {mod}\n')
        return textwrap.dedent(ret)

    def workspaces(self) -> str:
        ret = ''
        for index, ws in enumerate(self.cfg['ws_list']):
            ret += f'set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
        return textwrap.dedent(ret)

    @staticmethod
    def scratchpad_hide_cmd(hide: bool) -> str:
        """ Returns cmd needed to hide scratchpad.
            Args:
                hide (bool): to hide target or not.
        """
        ret = ""
        if hide:
            ret = ", [con_id=__focused__] scratchpad show"
        return ret

    def rules(self) -> str:
        def fill_rules_dict(mod, cmd_dict) -> List:
            config = mod.cfg
            for tag in config:
                cmd_dict[tag] = []
                for attr in config[tag]:
                    for target_attr in ['class', 'instance', 'name', 'role']:
                        cmd_dict[tag].append(info(
                            config, tag, attr, target_attr
                        ))
            return cmd_dict

        def rules_bscratch() -> str:
            """ Create i3 match rules for all tags. """
            ret = ''
            bscratch = extension.get_mods()['bscratch']
            cmd_dict = fill_rules_dict(bscratch, {})

            for tag in cmd_dict:
                rules = list(filter(lambda str: str != '', cmd_dict[tag]))
                if rules:
                    ret += f'set $bscratch-{tag} [' + ' '.join(rules) + ']'
                    ret += '\n'

            ret += '\n'
            for tag in cmd_dict:
                geom = bscratch.nsgeom.get_geom(tag)
                ret += f'for_window $bscratch-{tag} move scratchpad, {geom}'
                ret += '\n'

            return ret

        def rules_circle() -> str:
            ret = ''
            circle = extension.get_mods()['circle']
            cmd_dict = fill_rules_dict(circle, {})

            for tag in cmd_dict:
                rules = list(filter(lambda str: str != '', cmd_dict[tag]))
                ret += f'set $circle-{tag} [' + ' '.join(rules) + ']\n'

            ret += '\n'

            for tag in circle.cfg:
                focus_cmd = ''
                ws = circle.cfg[tag].get('ws', '')
                focus = bool(circle.cfg[tag].get('focus', True))
                if focus:
                    focus_cmd = ', focus'
                if ws:
                    ret += f'for_window $circle-{tag}' \
                        f' move workspace ${ws}{focus_cmd}\n'

            return ret

        def info(config: dict, tag: str, attr: str, target_attr: str) -> str:
            """ Create rule in i3 commands format
                Args:
                    config (dict): extension config.
                    tag (str): target tag.
                    attr (str): tag attrubutes.
                    target_attr (str): attribute to fill.
            """
            attr_name = {
                'class': 'class',
                'instance': 'instance',
                'name': 'window_name',
                'role': 'window_role'
            }
            cmd = ''
            if target_attr in attr:
                if not attr.endswith('_r'):
                    win_attr = attr_name[attr]
                else:
                    win_attr = attr_name[attr[:-2]]
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

        def plain_rules() -> str:
            return """
            for_window [instance="^(gpartedbin|recoll|gnome-disks)$"] move workspace $sys, floating enable, focus
            for_window [title="^Java iKVM Viewer.*$"] move workspace $remote, focus
            for_window [class="spotify"] move workspace $spotify, focus
            for_window [class="^(Lxappearance|Conky|Xmessage|XFontSel|gcolor2|Gcolor3|rdesktop|Arandr)$"] floating enable
            for_window [class="^(draw|inkscape|gimp)$"] move workspace $draw
            for_window [class=".*"] title_format "<span foreground='#395573'> >_ </span> %title", border pixel 3
            """

        ret = ''
        ret += \
            textwrap.dedent(rules_bscratch()) + \
            textwrap.dedent(rules_circle()) + \
            textwrap.dedent(plain_rules())
        return textwrap.dedent(ret)


    def keybindings_mode_start(self, name) -> str:
        return 'mode ' + name + ' {\n'

    def keybindings_mode_end(self) -> str:
        def bind_data() -> str:
            ret = ''
            bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
            for keybind in bindings:
                ret += f'bindsym {keybind} $exit\n'
            return ret
        return bind_data() + '}\n'

    def keybindings_mode_binding(self, keymap, name) -> str:
        return f'bindsym {keymap} mode "{name}"\n'

    def keybindings_mode_resize(self) -> str:
        mode_bind = 'Mod4+r'
        mode_name = 'RESIZE'

        def bind_data():
            return """
            bindsym h $win_action resize left 4
            bindsym j $win_action resize bottom 4
            bindsym k $win_action resize top 4
            bindsym l $win_action resize right 4
            bindsym Shift+h $win_action resize left -4
            bindsym Shift+j $win_action resize bottom -4
            bindsym Shift+k $win_action resize top -4
            bindsym Shift+l $win_action resize right 4

            bindsym a $win_action resize left 4
            bindsym s $win_action resize bottom 4
            bindsym w $win_action resize top 4
            bindsym d $win_action resize right 4
            bindsym Shift+a $win_action resize left -4
            bindsym Shift+s $win_action resize bottom -4
            bindsym Shift+w $win_action resize top -4
            bindsym Shift+d $win_action resize right -4

            bindsym semicolon resize shrink right 4
            bindsym Shift+colon resize grow right 4
            """

        ret = ''
        ret += self.keybindings_mode_binding(mode_bind, mode_name)
        ret += self.keybindings_mode_start(mode_name)
        ret += str(bind_data())
        ret += str(self.keybindings_mode_end())

        return textwrap.dedent(ret)

    def keybindings_mode_spec(self) -> str:
        mode_bind = 'Mod1+e'
        mode_name = 'SPEC'

        def bind_data():
            return """
            bindsym c exec rofi-pass; $exit
            bindsym e [urgent=latest] focus, $exit

            bindsym Shift+d floating toggle, $exit
            bindsym Shift+l exec sh -c 'sudo gllock', $exit

            bindsym o $menu pulse_output, $exit
            bindsym i $menu pulse_input, $exit
            bindsym Shift+t $exit, $menu gtk_theme
            bindsym Shift+i $exit, $menu icon_theme
            """

        ret = ''
        ret += self.keybindings_mode_binding(mode_bind, mode_name)
        ret += self.keybindings_mode_start(mode_name)
        ret += str(bind_data())
        ret += str(self.bscratch_bindings(mode_name))
        ret += str(self.circle_bindings(mode_name))
        ret += self.keybindings_mode_end()

        return textwrap.dedent(ret)

    def keybindings_mode_wm(self) -> str:
        mode_bind = 'Mod4+minus'
        mode_name = 'WM'

        def bind_data() -> str:
            return """
            bindsym grave layout default; $exit
            bindsym t layout tabbed; $exit
            bindsym minus layout splith; $exit
            bindsym backslash layout splitv; $exit

            bindsym j split vertical; $exit
            bindsym k split vertical; $exit
            bindsym h split horizontal; $exit
            bindsym l split horizontal; $exit

            bindsym m $menu xprop, $exit

            bindsym w move up
            bindsym a move left
            bindsym s move down
            bindsym d move right

            bindsym Shift+w $win_action x2 hup
            bindsym Shift+a $win_action x2 vleft
            bindsym Shift+s $win_action x2 hdown
            bindsym Shift+d $win_action x2 vright

            bindsym 1 $win_action quad 1
            bindsym 2 $win_action quad 2
            bindsym 3 $win_action quad 3
            bindsym 4 $win_action quad 4

            bindsym m $win_action maximize
            bindsym Shift+m $win_action revert_maximize
            bindsym x $win_action maxhor
            bindsym y $win_action maxvert
            bindsym Shift+x $win_action revert_maximize
            bindsym Shift+y $win_action revert_maximize
            bindsym Shift+plus $win_action grow
            bindsym Shift+minus $win_action shrink
            bindsym c $win_action center none
            bindsym Shift+c $win_action center resize

            bindsym Control+a layout toggle all
            bindsym Control+3 layout toggle all
            bindsym Control+s layout toggle split
            bindsym Control+t layout toggle
            """

        ret = ''
        ret += self.keybindings_mode_binding(mode_bind, mode_name)
        ret += self.keybindings_mode_start(mode_name)
        ret += str(bind_data())
        ret += str(self.bscratch_bindings(mode_name))
        ret += str(self.circle_bindings(mode_name))
        ret += self.keybindings_mode_end()

        return textwrap.dedent(ret)

    def keybindings_mode_default(self) -> str:
        mode_name = 'default'

        def bind_data() -> str:
            return """
            bindsym Mod4+q fullscreen toggle
            bindsym Mod4+p exec ~/bin/scripts/rofi_tmux_urls
            bindsym Mod4+Control+q kill

            bindsym Print exec --no-startup-id ~/bin/scripts/screenshot
            bindsym Mod4+Shift+d exec --no-startup-id "zsh -c '~/bin/scripts/dw s'"
            bindsym Mod4+Shift+0 exec --no-startup-id splatmoji type
            bindsym Mod4+Shift+l exec --no-startup-id "~/bin/scripts/rofi_lutris"
            bindsym Shift+Print exec --no-startup-id ~/bin/scripts/screenshot -c
            bindsym Control+Print exec --no-startup-id ~/bin/scripts/screenshot -r
            bindsym Mod4+Shift+3 exec --no-startup-id ~/bin/scripts/screenshot -r
            bindsym Mod4+Shift+4 exec --no-startup-id flameshot gui
            bindsym Mod4+Shift+t exec --no-startup-id ~/bin/clip translate
            bindsym Mod4+Shift+y exec --no-startup-id "~/bin/clip youtube-dw-list"
            bindsym Mod4+m exec --no-startup-id ~/bin/scripts/rofi_mpd.py
            bindsym Mod4+Shift+i exec --no-startup-id ~/bin/scripts/rofi_networkmanager

            bindsym Mod4+apostrophe exec zsh -c ${XDG_CONFIG_HOME}/i3/bin/i3_reload
            bindsym Mod4+Shift+apostrophe exec zsh -c ${XDG_CONFIG_HOME}/i3/bin/i3_restart

            bindsym Mod4+h focus left
            bindsym Mod4+l focus right
            bindsym Mod4+j focus down
            bindsym Mod4+k focus up

            bindsym XF86AudioLowerVolume $volume d
            bindsym XF86AudioRaiseVolume $volume u

            bindsym Mod4+Control+Shift+R $bscratch geom_restore
            bindsym Mod4+Control+Shift+D $bscratch geom_dump
            bindsym Mod4+Control+Shift+S $bscratch geom_autosave
            bindsym Mod4+Control+a $bscratch dialog
            bindsym Mod4+3 $bscratch next
            bindsym Mod4+s $bscratch hide_current

            bindsym Mod1+g $menu goto_win
            bindsym Mod4+Shift+a $menu attach
            bindsym Mod4+g $menu ws
            bindsym Mod4+Control+g $menu movews
            bindsym Mod4+Control+grave $menu cmd_menu
            bindsym Mod4+Shift+s $menu autoprop

            bindsym Mod1+Tab $win_history switch
            bindsym Mod4+slash $win_history switch
            bindsym Mod4+grave $win_history focus_next_visible
            bindsym Mod4+Shift+grave $win_history focus_prev_visible
            """

        ret = ''
        ret += str(textwrap.dedent(bind_data()))
        ret += str(self.bscratch_bindings(mode_name))
        ret += str(self.circle_bindings(mode_name))

        return textwrap.dedent(ret)

