import subprocess
import pulsectl


class pulse_menu():
    def __init__(self, menu):
        self.menu = menu

    def pulseaudio_output(self):
        self.pulse = pulsectl.Pulse('neg-pulse-selector')

        self.pulse_data = {
            "app_list": [],
            "sink_output_list": [],
            "app_props": {},
            "pulse_sink_list": self.pulse.sink_list(),
            "pulse_app_list": self.pulse.sink_input_list(),
        }

        for app in self.pulse_data["pulse_app_list"]:
            app_name = app.proplist["media.name"] + ' -- ' + \
                app.proplist["application.name"]
            self.pulse_data["app_list"] += [app_name]
            self.pulse_data["app_props"][app_name] = app

        if self.pulse_data["app_list"] > 0:
            app_ret = self.pulseaudio_select_app()
            if self.pulse_data["sink_output_list"] > 0:
                self.pulseaudio_select_output(app_ret)

    def pulseaudio_input(self):
        pass

    def pulseaudio_select_app(self):
        rofi_params = {
            'cnum': 1,
            'lnum': len(self.pulse_data["app_list"]),
            'auto_selection': '-auto-select',
            'width': int(self.menu.screen_width * 0.55),
            'prompt': f'{self.menu.wrap_str("pulse app")} {self.menu.prompt}',
        }
        rofi_app_sel = subprocess.run(
            self.menu.rofi_args(rofi_params),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(self.pulse_data["app_list"]), 'UTF-8')
        ).stdout

        if rofi_app_sel is not None:
            app_ret = rofi_app_sel.decode('UTF-8').strip()

        exclude_device_name = ""
        sel_app_props = \
            self.pulse_data["app_props"][app_ret].proplist
        for stream in self.pulse.stream_restore_list():
            if stream is not None:
                if stream.device is not None:
                    if stream.name == sel_app_props['module-stream-restore.id']:
                        exclude_device_name = stream.device

        for _, sink in enumerate(self.pulse_data["pulse_sink_list"]):
            if sink.proplist.get('udev.id', ''):
                if sink.proplist['udev.id'].split('.')[0] == \
                        exclude_device_name.split('.')[1]:
                    continue
            if sink.proplist.get('device.profile.name', ''):
                if sink.proplist['device.profile.name'] == \
                        exclude_device_name.split('.')[-1]:
                    continue
            self.pulse_data["sink_output_list"] += \
                [str(sink.index) + ' -- ' + sink.description]

        return app_ret

    def pulseaudio_select_output(self, app_ret) -> None:
        rofi_params = {
            'cnum': 1,
            'lnum': len(self.pulse_data["sink_output_list"]),
            'auto_selection': '-auto-select',
            'width': int(self.menu.screen_width * 0.55),
            'prompt': f'{self.menu.wrap_str("pulse output")} {self.menu.prompt}'
        }
        rofi_output_sel = subprocess.run(
            self.menu.rofi_args(rofi_params),
            stdout=subprocess.PIPE,
            input=bytes(
                '\n'.join(self.pulse_data["sink_output_list"]),
                'UTF-8'
            )
        ).stdout

        if rofi_output_sel is not None:
            out_ret = rofi_output_sel.decode('UTF-8').strip()

        target_idx = out_ret.split('--')[0].strip()
        if int(self.pulse_data["app_props"][app_ret].index) is not None \
                and int(target_idx) is not None:
            self.pulse.sink_input_move(
                int(self.pulse_data["app_props"][app_ret].index),
                int(target_idx),
            )

