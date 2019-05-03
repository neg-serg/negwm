import os
import configparser
import subprocess


class gtk():
    def __init__(self, menu):
        self.menu = menu
        self.gtk_config = configparser.ConfigParser()

    def change_gtk_theme(self):
        gtk_themes_list = []
        for root, dirs, files in os.walk(os.path.expanduser("~/.themes")):
            for file in files:
                if file == 'gtk.css':
                    target_dir_path = os.path.join(root, os.pardir)
                    gtk_settings = self.gtk_config.read(
                        os.path.abspath(
                            os.path.join(target_dir_path, 'index.theme')
                        )
                    )
                    if gtk_settings:
                        gtk_themes_list += [os.path.basename(
                            os.path.abspath(target_dir_path)
                        )]

        ret = ""
        gtk_theme_sel = subprocess.run(
            self.menu.rofi_args(
                cnum=1,
                lnum=len(gtk_themes_list),
                width=int(self.screen_width * 0.55),
                prompt=f'{self.wrap_str("gtk_theme")} {self.prompt}'
            ),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(gtk_themes_list), 'UTF-8')
        ).stdout

        if gtk_theme_sel is not None:
            ret = gtk_theme_sel.decode('UTF-8').strip()

        if ret is not None and ret != '':
            subprocess.call([
                os.path.expanduser('~/bin/scripts/gnome_settings'), '-a', ret
            ])

