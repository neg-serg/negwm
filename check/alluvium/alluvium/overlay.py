import gi  # isort:skip

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # isort:skip

from .config import Config


class Overlay:
    STYLE = b"""
#overlay {
  background-color: @theme_bg_color;
  color: @theme_text_color;
}

.group {
  margin: 10px;
}

.heading {
  font-size: 1.2em;
}

.key {
  font-family: monospace;
  font-weight: normal;
  background-color: @insensitive_bg_color;
  border: 1px solid;
  border-color: @insensitive_base_color;
  color: @theme_unfocused_fg_color;

  padding: 2px;
  margin: 2px;
  font-size: .9em;
}
"""

    def __init__(self):
        window = Gtk.Window(title="alluvium - i3 keybindings", name="overlay")
        window.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        window.set_type_hint(Gtk.WindowType.POPUP)
        window.set_skip_taskbar_hint(True)
        window.set_skip_pager_hint(True)
        window.set_decorated(False)
        window.set_resizable(False)
        window.set_focus_on_map(False)
        window.set_deletable(False)
        window.set_accept_focus(False)
        window.stick()
        screen = window.get_screen()
        visual = screen.get_rgba_visual()
        window.set_visual(visual)

        self.window = window

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(Overlay.STYLE)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.box = Gtk.FlowBox(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.set_selection_mode(Gtk.SelectionMode.NONE)

        self.window.add(self.box)
        self.window.show_all()

    def render_group(self, name, bindings):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.get_style_context().add_class("group")
        heading = Gtk.Label(label=name)
        heading.get_style_context().add_class("heading")
        box.pack_start(heading, False, False, 0)

        for binding in bindings:
            line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            line.pack_start(Gtk.Label(label=binding.label), False, False, 0)
            keys = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            keys.get_style_context().add_class("keys")
            for key in binding.keys:
                key_label = Gtk.Label(label=key)
                key_label.get_style_context().add_class("key")
                keys.pack_start(key_label, False, False, 0)
            line.pack_end(keys, False, False, 0)
            box.pack_start(line, False, False, 0)

        return box

    def show_bindings(self, mode, config: Config):
        self.box.foreach(lambda label: label.destroy())

        # Ensure that the window shrinks when fewer keybindings are shown
        self.window.resize(1, 1)

        if mode == "default":
            for group, bindings in config.groups:
                self.box.add(self.render_group(group, bindings))
        else:
            matching = [bindings for name, bindings in config.modes if name == mode]
            if len(matching) > 0:
                self.box.add(self.render_group(mode, matching[0]))

        self.box.show_all()
