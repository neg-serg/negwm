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

    def show_cfg(self):
        print(''.join(self.generate()))

    def write_cfg(self):
        i3_config = '/home/neg/.config/i3/_config'
        with open(i3_config, 'w', encoding='utf8') as outfile:
            outfile.write('\n'.join(self.generate()))

    def autostart(self):
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

    def scratchpad_dialog(self):
        return 'set $scratchpad_dialog move scratchpad, move position 180 20, resize set 1556 620'

    def gaps(self):
        return """
        gaps inner  0
        gaps outer  0
        gaps top    0
        gaps bottom 0
        """

    def general(self):
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

    def colorscheme(self):
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

    def font(self):
        return """
        set $myfont Iosevka Term Heavy 9
        font pango: $myfont
        """

    def mods_commands(self) -> str:
        ret = ''
        for mod in sorted(extension.get_mods()):
            ret += (f'set ${mod} exec --no-startup-id {self.send_path} {mod}\n')
        return ret

    def workspaces(self):
        ret = ''
        for index, ws in enumerate(self.cfg['ws_list']):
            ret += f'set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
        return ret

    def rules(self):
        return """
        #-- wm class groups
        set $browsers [class="^(firefox|Chromium|Yandex-browser-beta|Tor Browser)$"]
        set $sclient [class="^(Steam|steam)$"]
        set $games [class="^(steam_app.*|PillarsOfEternityII|lutris|Lutris)$"]
        set $wine_apps [class="^(Wine|wine|Crossover)$"]
        set $windows_exe_by_title [title="^.*.exe$"]
        set $windows_exe_by_class [class="^.*.exe$"]
        set $pdf [class="Zathura"]
        set $fb2 [class="Cr3" instance="cr3"]
        set $mplayer [class="^(MPlayer|mpv|vaapi|vdpau)$"]
        set $webcam [class="^(cheese|obs)$"]
        set $vim [instance="nwim"]
        set $vms [class="(?i)^(VirtualBox|vmware|looking-glass-client|[Qq]emu.*|spic).*$"]
        set $daw [class="Bitwig Studio" instance="^(airwave-host-32.exe|Bitwig Studio)$"]

        #-- wm rules
        for_window $browsers move workspace $web, focus
        for_window $vms move workspace $vm, focus
        for_window [{class,instance}="^term$"] move workspace $term, focus
        for_window $mplayer move workspace $gfx, focus
        for_window [class="spotify"] move workspace $spotify, focus
        for_window [class="Sxiv"] move workspace $pic, focus
        for_window [instance="^(gpartedbin|recoll|gnome-disks)$"] move workspace $sys, floating enable, focus
        for_window [instance="^(xfreerdp|remmina|org.remmina.Remmina)$"] move workspace $remote, focus
        for_window [title="^Java iKVM Viewer.*$"] move workspace $remote, focus
        for_window $daw move workspace $sound, focus

        #-- readers
        for_window {$fb2,$pdf}, move workspace $doc, focus
        #-- various floating
        for_window [class="^(Lxappearance|Conky|Xmessage|XFontSel|gcolor2|Gcolor3|rdesktop|Arandr)$"] floating enable
        #-- graphics
        for_window [class="^(draw|inkscape|gimp)$"] move workspace $draw
        #-- editors
        for_window $vim move workspace $dev, focus
        #-- games
        for_window $sclient move workspace $steam, focus
        for_window $games move workspace $steam, focus
        #-- dialogs
        for_window [window_role="^(GtkFileChooserDialog|Organizer|Manager)$"] $scratchpad_dialog
        for_window [class="Places"] $scratchpad_dialog
        """

    def keybindings_mode_resize(self):
        return """
        bindsym Mod4+r mode "RESIZE"  # resize mode
        mode "RESIZE" {
            bindsym {h,Shift+h} $win_action resize left {4,-4}
            bindsym {j,Shift+j} $win_action resize bottom {4,-4}
            bindsym {k,Shift+k} $win_action resize top {4,-4}
            bindsym {l,Shift+l} $win_action resize right {4,-4}

            bindsym {a,Shift+a} $win_action resize left {4,-4}
            bindsym {s,Shift+s} $win_action resize bottom {4,-4}
            bindsym {w,Shift+w} $win_action resize top {4,-4}
            bindsym {d,Shift+d} $win_action resize right {4,-4}

            #-------------------------------------------------------
            bindsym {semicolon,Shift+colon} resize {shrink,grow} right 4
            bindsym {Return,Escape,space,Control+C,Control+G} $exit
        }
        """

    def keybindings_mode_spec(self):
        return """
        #-- mode: special
        bindsym Mod1+e mode "SPEC"   # special mode
        mode "SPEC" {
            bindsym c exec rofi-pass; $exit
            bindsym e $exit, [urgent=latest] focus
            bindsym a $exit, $bscratch dialog

            bindsym 5 $exit, $circle subtag web tor
            bindsym y $exit, $circle subtag web yandex
            bindsym f $exit, $circle subtag web firefox

            bindsym Shift+t $exit, $menu gtk_theme
            bindsym Shift+i $exit, $menu icon_theme

            bindsym Shift+d floating toggle; $exit
            bindsym Shift+l exec sh -c 'sudo gllock'; $exit
            bindsym v exec ~/bin/qemu/vm_menu; $exit
            bindsym Shift+v exec ~/bin/qemu/vm_menu start_win10; $exit
            bindsym o $menu pulse_output; $exit
            bindsym i $menu pulse_input; $exit

            bindsym Mod4+s $bscratch subtag im skype, $exit
            bindsym Mod1+s $bscratch subtag im skype, $exit
            bindsym s $bscratch subtag im skype, $exit
            bindsym Mod4+t $bscratch subtag im tel, $exit
            bindsym Mod1+t $bscratch subtag im tel, $exit
            bindsym t $bscratch subtag im tel, $exit
            bindsym m $bscratch toggle neomutt, $exit
            bindsym w $bscratch toggle webcam, $exit
            bindsym Shift+r $bscratch toggle ranger, $exit

            bindsym {Return,Escape,Control+C,Control+G} $exit
        }
        """

    def keybindings_mode_wm(self):
        return """
        bindsym Mod4+minus mode "WM"  # window-manager / split / tiling mode
        #-- mode: window manager
        mode "WM" {
            bindsym grave layout default; $exit
            bindsym t layout tabbed; $exit
            bindsym minus layout splith; $exit
            bindsym backslash layout splitv; $exit
            bindsym j split vertical; $exit
            bindsym k split vertical; $exit
            bindsym h split horizontal; $exit
            bindsym l split horizontal; $exit
            bindsym m $menu xprop, $exit
            bindsym {w,a,s,d} move {up,left,down,right}

            #-- win_action
            bindsym m $win_action maximize
            bindsym Shift+m $win_action revert_maximize
            bindsym {x,y} $win_action {maxhor,maxvert}
            bindsym Shift+x $win_action revert_maximize
            bindsym Shift+y $win_action revert_maximize
            bindsym {1,2,3,4} $win_action quad {1,2,3,4}
            bindsym Shift+{w,a,s,d} $win_action x2 {hup,vleft,hdown,vright}
            bindsym Shift+{plus,minus} $win_action {grow,shrink}
            bindsym c $win_action center none
            bindsym Shift+c $win_action center resize

            bindsym g mode "GAPS"

            bindsym Control+a layout toggle all
            bindsym Control+3 layout toggle all
            bindsym Control+s layout toggle split
            bindsym Control+t layout toggle

            bindsym {Return,Escape,Control+C,Control+G} $exit
        }
        """

    def keybindings_mode_gaps(self):
        return """
        mode "GAPS" {
            bindsym {o,i} mode gaps-{outer,inner}
            bindsym {Return,Escape,Control+C,Control+G} $exit
        }

        mode "GAPS-OUTER" {
            bindsym {plus,minus}     gaps outer current {plus,minus} 5
            bindsym 0                gaps outer current set 0

            bindsym Shift+{plus,minus}  gaps outer all {plus,minus} 5
            bindsym Shift+0             gaps outer all set 0

            bindsym {Return,Escape,Control+C,Control+G} $exit
        }

        mode "GAPS-INNER" {
            bindsym {plus,minus}     gaps inner current {plus,minus} 5
            bindsym 0                gaps inner current set 0

            bindsym Shift+{plus,minus}  gaps inner all {plus,minus} 5
            bindsym Shift+0             gaps inner all set 0

            bindsym {Return,Escape,Control+C,Control+G} $exit
        }
        """

    def keybindings(self):
        return """
        #-- keybindings
        set $exit mode "default"
        bindsym Mod4+q fullscreen toggle
        bindsym XF86Audio{Lower,Raise}Volume $volume {d,u}
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

        bindsym Mod4+apostrophe exec zsh -c ${XDG_CONFIG_HOME}/i3/bin/i3_reload
        bindsym Mod4+Shift+apostrophe exec zsh -c ${XDG_CONFIG_HOME}/i3/bin/i3_restart

        #-- named scratchpad
        bindsym Mod4+f $bscratch toggle ncmpcpp
        bindsym Mod4+e $bscratch toggle im
        bindsym Mod4+d $bscratch toggle teardrop
        bindsym Mod4+a $bscratch toggle youtube
        bindsym Mod4+Shift+p $bscratch toggle volcontrol
        bindsym Mod4+v $bscratch toggle discord

        bindsym Mod4+Control+Shift+R $bscratch geom_restore
        bindsym Mod4+Control+Shift+D $bscratch geom_dump
        bindsym Mod4+Control+Shift+S $bscratch geom_autosave
        bindsym Mod4+3 $bscratch next
        bindsym Mod4+s $bscratch hide_current

        #-- circle
        bindsym Mod4+Control+c $circle next sxiv
        bindsym Mod4+Shift+c $circle subtag sxiv wallpaper
        bindsym Mod4+x $circle next term
        bindsym Mod4+1 $circle next nwim
        bindsym Mod4+Control+v $circle next vm
        bindsym Mod4+Control+e $circle next lutris
        bindsym Mod4+Shift+e $circle next steam
        bindsym Mod4+Control+f $circle next looking_glass
        bindsym Mod4+w $circle next web
        bindsym Mod4+b $circle next vid
        bindsym Mod4+o $circle next doc
        bindsym Mod4+Shift+o $circle next obs
        bindsym Mod4+Control+5 $circle next remote
        bindsym Mod4+Control+b $circle next bitwig

        #-- window actions
        bindsym Mod4+grave $win_history focus_next_visible
        bindsym Mod4+Shift+grave $win_history focus_prev_visible

        bindsym Mod4+{h,l,j,k} focus {left,right,down,up}

        #-- menu
        bindsym Mod1+g $menu goto_win
        bindsym Mod4+m exec --no-startup-id ~/bin/scripts/rofi_mpd.py
        bindsym Mod4+Shift+i exec --no-startup-id ~/bin/scripts/rofi_networkmanager
        bindsym Mod4+Shift+a $menu attach
        bindsym Mod4+g $menu ws
        bindsym Mod4+Control+g $menu movews
        bindsym Mod4+Control+grave $menu cmd_menu
        bindsym Mod4+Shift+s $menu autoprop

        bindsym Mod1+Tab $win_history switch
        bindsym Mod4+slash $win_history switch
        """
