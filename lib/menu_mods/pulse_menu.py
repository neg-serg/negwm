import subprocess
import pulsectl
import shutil


class pulse_menu():
    def __init__(self, menu):
        self.menu = menu
        self.pulse_data = {}
        if shutil.which('pulseaudio') is None:
            self.pulse = None
            return

        check_pulseaudio = subprocess.run(['pulseaudio', '--check'],
            check=False,
            capture_output=True
        )
        if check_pulseaudio.returncode == 0:
            try:
                self.pulse = pulsectl.Pulse('neg-pulse-selector')
            except Exception:
                self.pulse = None

    def pulse_data_init(self):
        self.pulse_data = {
            "app_list": [],
            "sink_output_list": [],
            "app_props": {},
            "pulse_sink_list": self.pulse.sink_list(),
            "pulse_app_list": self.pulse.sink_input_list(),
        }

    def pulseaudio_mute(self, mute):
        self.pulse_data_init()
        self.fill_output_list(False)
        target_idx = self.pulseaudio_select_output()
        if mute and target_idx:
            self.pulse.sink_mute(int(target_idx), bool(int(mute)))

    def pulseaudio_output(self):
        if self.pulse is None:
            return

        self.pulse_data_init()
        for app in self.pulse_data["pulse_app_list"]:
            app_name = app.proplist["media.name"] + ' -- ' + \
                app.proplist["application.name"]
            self.pulse_data["app_list"] += [app_name]
            self.pulse_data["app_props"][app_name] = app
        if self.pulse_data["app_list"]:
            app_ret = self.pulseaudio_select_app()
            if self.pulse_data["sink_output_list"]:
                target_idx = self.pulseaudio_select_output()
                if target_idx:
                    self.pulseaudio_move_output(app_ret, target_idx)

    def pulseaudio_input(self):
        if self.pulse is None:
            return

    def fill_output_list(self, exclude_current_dev, app_ret=None):
        for _, sink in enumerate(self.pulse_data["pulse_sink_list"]):
            if exclude_current_dev and self.current_device_name(sink, app_ret):
                continue
            self.pulse_data["sink_output_list"] += \
                [str(sink.index) + ' -- ' + sink.description]

    def pulseaudio_select_app(self, exclude_current_dev=True):
        if self.pulse is None:
            return 0

        menu_params = {
            'cnum': 1,
            'lnum': len(self.pulse_data["app_list"]),
            'auto_selection': '-auto-select',
            'width': int(self.menu.screen_width * 0.55),
            'prompt': f'{self.menu.wrap_str("pulse app")} \
            {self.menu.conf("prompt")}',
        }
        menu_app_sel = subprocess.run(
            self.menu.args(menu_params),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(self.pulse_data["app_list"]), 'UTF-8'),
            check=False
        ).stdout
        app_ret = None
        if menu_app_sel is not None:
            app_ret = menu_app_sel.decode('UTF-8').strip()
        if app_ret is None or not app_ret:
            return ""

        self.fill_output_list(exclude_current_dev, app_ret)
        return app_ret

    def get_exclude_device_name(self, app_ret):
        sel_app_props = \
            self.pulse_data["app_props"][app_ret].proplist
        for stream in self.pulse.stream_restore_list():
            if stream is not None:
                if stream.device is not None:
                    if stream.name == sel_app_props['module-stream-restore.id']:
                        return stream.device

        return None

    def current_device_name(self, sink, app_ret):
        exclude_device_name = self.get_exclude_device_name(app_ret)
        if exclude_device_name is not None and exclude_device_name:
            if sink.proplist.get('udev.id', ''):
                if sink.proplist['udev.id'].split('.')[0] == \
                        exclude_device_name.split('.')[1]:
                    return True

            if sink.proplist.get('device.profile.name', ''):
                if sink.proplist['device.profile.name'] == \
                        exclude_device_name.split('.')[-1]:
                    return True

        return False

    def pulseaudio_select_output(self):
        """ Create params for pulseaudio selector """
        if self.pulse is None:
            return None

        menu_params = {
            'cnum': 1,
            'lnum': len(self.pulse_data["sink_output_list"]),
            'auto_selection': '-auto-select',
            'width': int(self.menu.screen_width * 0.55),
            'prompt':
                f'{self.menu.wrap_str("pulse output")} \
                {self.menu.conf("prompt")}'
        }
        menu_output_sel = subprocess.run(
            self.menu.args(menu_params),
            stdout=subprocess.PIPE,
            input=bytes(
                '\n'.join(self.pulse_data["sink_output_list"]),
                'UTF-8'
            ),
            check=False
        ).stdout
        target_idx = '0'
        if menu_output_sel is not None:
            out_ret = menu_output_sel.decode('UTF-8').strip()
            target_idx = out_ret.split('--')[0].strip()
        return target_idx

    def pulseaudio_move_output(self, app_ret, target_idx):
        """ Move selected input for the given application """
        if int(self.pulse_data["app_props"][app_ret].index) is not None \
                and target_idx and int(target_idx) is not None:
            self.pulse.sink_input_move(
                int(self.pulse_data["app_props"][app_ret].index),
                int(target_idx),
            )
