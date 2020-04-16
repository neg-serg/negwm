#!/usr/bin/python3

from cfg import cfg
from extension import extension
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
            'exec_always zsh -c ${XDG_CONFIG_HOME}/i3/bin/negi3wm_run &',
            'exec_always pkill sxhkd; sxhkd &',
            "exec_always pkill -f 'mpc idle'",
            "exec caffeine &",
            "exec_always ~/bin/scripts/gnome_settings &",
            "exec /usr/lib/gsd-xsettings &",
            "exec_always ~/bin/scripts/panel_run.sh hard",
            "exec /usr/sbin/gpaste-client daemon",
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

        focus_follows_mouse no
        force_display_urgency_hint 0 ms
        focus_on_window_activation urgent

        #-- warp the mouse to the middle of the window when changing to a different screen
        mouse_warping none
        focus_wrapping yes

        title_align left
        for_window [class=".*"] title_format "<span foreground='#395573'> >_ </span> %title"
        for_window [class="^.*"] border pixel 3

        show_marks yes
        smart_borders on
        hide_edge_borders both
        """

    def colorscheme(self) -> str:
        return """
        # 1 :: border
        # 2 :: background active
        # 3 :: foreground inactive
        # 4 :: background inactive
        # 5 :: indicator

        client.focused                 #222233  #000000  #ddddee  #112211 #0C0C0D
        client.focused_inactive        #000000  #000000  #005fff  #000000 #222233
        client.unfocused               #000000  #000000  #315c70  #000000 #222233
        client.urgent                  #000000  #2E2457  #4C407C  #32275E #32275E
        client.placeholder             #000000  #0c0c0c  #ffffff  #000000 #0c0c0c
        client.background              #000000
        """

    def bscratch_bindings(self, mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p) -> str:
            ret = ''
            pref = ''
            if mode != 'default':
                pref = '\t'
            get_binds = p.split('_')
            mode_ = get_binds[1]
            cmd = get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    for keybind in settings[p]:
                        ret += f'{pref}bindsym {keybind} $bscratch {cmd} {tag}\n'
            return ret

        bscratch = extension.get_mods()['bscratch']
        for tag,settings in bscratch.cfg.items():
            if tag != "transients":
                for param in settings:
                    if isinstance(settings[param], dict):
                        for p in settings[param]:
                            if p.startswith('keybind_'):
                                ret += get_binds(mode, tag, settings[param], p)
                    elif param.startswith('keybind_'):
                        ret += get_binds(mode, tag, settings, param)
        return ret

    def circle_bindings(self, mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p) -> str:
            ret = ''
            pref = ''
            if mode != 'default':
                pref = '\t'
            get_binds = p.split('_')
            mode_ = get_binds[1]
            cmd = get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    for keybind in settings[p]:
                        ret += f'{pref}bindsym {keybind} $circle {cmd} {tag}\n'
            return ret

        circle = extension.get_mods()['circle']
        for tag,settings in circle.cfg.items():
            for param in settings:
                if isinstance(settings[param], dict):
                    for p in settings[param]:
                        if p.startswith('keybind_'):
                            ret += get_binds(mode, tag, settings[param], p)
                elif param.startswith('keybind_'):
                    ret += get_binds(mode, tag, settings, param)
        return ret

    def font(self) -> str:
        return "font pango: Iosevka Term Heavy 9"

    def mods_commands(self) -> str:
        ret = ''
        for mod in sorted(extension.get_mods()):
            ret += (f'set ${mod} exec --no-startup-id {self.send_path} {mod}\n')
        return ret

    def workspaces(self) -> str:
        ret = ''
        for index, ws in enumerate(self.cfg['ws_list']):
            ret += f'set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
        return ret

    def rules(self) -> str:
        def rules_groups_define_circle() -> str:
            return """
            set $browsers [class="^(firefox|Chromium|Yandex-browser-beta|Tor Browser)$"]
            set $sclient [class="^(Steam|steam)$"]
            set $games [class="^(steam_app.*|PillarsOfEternityII|lutris|Lutris)$"]
            set $pdf [class="Zathura"]
            set $fb2 [class="Cr3" instance="cr3"]
            set $mplayer [class="^(MPlayer|mpv|vaapi|vdpau)$"]
            set $vim [instance="nwim"]
            set $vms [class="(?i)^(VirtualBox|vmware|looking-glass-client|[Qq]emu.*|spic).*$"]
            set $daw [class="Bitwig Studio" instance="^(airwave-host-32.exe|Bitwig Studio)$"]
            """

        def rules_groups_define_standalone() -> str:
            return  """
            set $webcam [class="cheese"]
            set $webcam [class="^obs"]

            set $scratchpad_dialog move scratchpad, move position 180 20, resize set 1556 620
            """

        def plain_rules() -> str:
            return """
            for_window $browsers move workspace $web, focus
            for_window $vms move workspace $vm, focus
            for_window [class="^term$"] move workspace $term, focus
            for_window [instance="^term$"] move workspace $term, focus
            for_window $mplayer move workspace $gfx, focus
            for_window [class="Sxiv"] move workspace $pic, focus
            for_window $daw move workspace $sound, focus

            for_window [instance="^(gpartedbin|recoll|gnome-disks)$"] move workspace $sys, floating enable, focus
            for_window [title="^Java iKVM Viewer.*$"] move workspace $remote, focus
            for_window [class="spotify"] move workspace $spotify, focus

            for_window $fb2 move workspace $doc, focus
            for_window $pdf move workspace $doc, focus
            for_window $vim move workspace $dev, focus
            for_window $sclient move workspace $steam, focus
            for_window $games move workspace $steam, focus
            for_window [class="^(Lxappearance|Conky|Xmessage|XFontSel|gcolor2|Gcolor3|rdesktop|Arandr)$"] floating enable
            for_window [class="^(draw|inkscape|gimp)$"] move workspace $draw
            """

        def scratchpad_dialog() -> str:
            return """
            for_window [window_role="^(GtkFileChooserDialog|Organizer|Manager)$"] $scratchpad_dialog
            for_window [class="Places"] $scratchpad_dialog
            """

        ret = ''
        ret += rules_groups_define_standalone() + \
            rules_groups_define_circle() + \
            plain_rules() + \
            scratchpad_dialog()
        return ret


    def keybindings_mode_start(self, name) -> str:
        return 'mode ' + name + ' {\n'

    def keybindings_mode_end(self) -> str:
        return 'bindsym {Return,Escape,space,Control+C,Control+G} $exit\n' + '}\n'

    def keybindings_mode_binding(self, keymap, name) -> str:
        return f'bindsym {keymap} mode "{name}"\n'

    def keybindings_mode_resize(self) -> str:
        mode_bind = 'Mod4+r'
        mode_name = 'RESIZE'

        def bind_data():
            return """
            bindsym {h,Shift+h} $win_action resize left {4,-4}
            bindsym {j,Shift+j} $win_action resize bottom {4,-4}
            bindsym {k,Shift+k} $win_action resize top {4,-4}
            bindsym {l,Shift+l} $win_action resize right {4,-4}

            bindsym {a,Shift+a} $win_action resize left {4,-4}
            bindsym {s,Shift+s} $win_action resize bottom {4,-4}
            bindsym {w,Shift+w} $win_action resize top {4,-4}
            bindsym {d,Shift+d} $win_action resize right {4,-4}

            bindsym {semicolon,Shift+colon} resize {shrink,grow} right 4
            """

        ret = ''
        ret += self.keybindings_mode_binding(mode_bind, mode_name)
        ret += self.keybindings_mode_start(mode_name)
        ret += str(bind_data())
        ret += self.keybindings_mode_end()

        return ret

    def keybindings_mode_spec(self) -> str:
        mode_bind = 'Mod1+e'
        mode_name = 'SPEC'

        def bind_data():
            return """
            bindsym c exec rofi-pass; $exit
            bindsym e $exit, [urgent=latest] focus

            bindsym Shift+d floating toggle; $exit
            bindsym Shift+l exec sh -c 'sudo gllock'; $exit
            bindsym v exec ~/bin/qemu/vm_menu; $exit
            bindsym Shift+v exec ~/bin/qemu/vm_menu start_win10; $exit

            bindsym o $menu pulse_output; $exit
            bindsym i $menu pulse_input; $exit
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

        return ret

    def keybindings_mode_wm(self) -> str:
        mode_bind = 'Mod4+minus'
        mode_name = 'WM'

        def bind_data() -> str:
            return """
            bindsym grave layout default; $exit
            bindsym t layout tabbed; $exit
            bindsym minus layout splith; $exit
            bindsym backslash layout splitv; $exit
            bindsym {j,k} split vertical; $exit
            bindsym {h,l} split horizontal; $exit
            bindsym m $menu xprop, $exit
            bindsym {w,a,s,d} move {up,left,down,right}

            bindsym m $win_action maximize
            bindsym Shift+m $win_action revert_maximize
            bindsym {x,y} $win_action {maxhor,maxvert}
            bindsym Shift+{x,y} $win_action revert_maximize
            bindsym {1,2,3,4} $win_action quad {1,2,3,4}
            bindsym Shift+{w,a,s,d} $win_action x2 {hup,vleft,hdown,vright}
            bindsym Shift+{plus,minus} $win_action {grow,shrink}
            bindsym c $win_action center none
            bindsym Shift+c $win_action center resize

            bindsym Control+{a,3} layout toggle all
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

        return ret

    def keybindings_mode_default(self) -> str:
        return str("""
        set $exit mode "default"

        bindsym Mod4+q fullscreen toggle
        bindsym Mod4+p exec ~/bin/scripts/rofi_tmux_urls
        bindsym Mod4+Control+q kill

        bindsym Print exec --no-startup-id ~/bin/scripts/screenshot
        bindsym Mod4+Shift+d exec --no-startup-id "zsh -c '~/bin/scripts/dw s'"
        bindsym Mod4+Shift+y exec --no-startup-id "~/bin/clip youtube-dw-list"
        bindsym Mod4+Shift+0 exec --no-startup-id splatmoji type
        bindsym Mod4+Shift+l exec --no-startup-id "~/bin/scripts/rofi_lutris"
        bindsym Shift+Print exec --no-startup-id ~/bin/scripts/screenshot -c
        bindsym Control+Print exec --no-startup-id ~/bin/scripts/screenshot -r
        bindsym Mod4+Shift+3 exec --no-startup-id ~/bin/scripts/screenshot -r
        bindsym Mod4+Shift+4 exec --no-startup-id flameshot gui
        bindsym Mod4+Shift+t exec --no-startup-id ~/bin/clip translate
        bindsym Mod4+m exec --no-startup-id ~/bin/scripts/rofi_mpd.py
        bindsym Mod4+Shift+i exec --no-startup-id ~/bin/scripts/rofi_networkmanager

        bindsym Mod4+apostrophe exec zsh -c ${XDG_CONFIG_HOME}/i3/bin/i3_reload
        bindsym Mod4+Shift+apostrophe exec zsh -c ${XDG_CONFIG_HOME}/i3/bin/i3_restart

        bindsym Mod4+{h,l,j,k} focus {left,right,down,up}

        bindsym XF86Audio{Lower,Raise}Volume $volume {d,u}

        bindsym Mod4+Control+Shift+R $bscratch geom_restore
        bindsym Mod4+Control+Shift+D $bscratch geom_dump
        bindsym Mod4+Control+Shift+S $bscratch geom_autosave
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
        """) + self.bscratch_bindings('default') + str(self.circle_bindings('default'))
