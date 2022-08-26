#!/bin/python

# Creates a rofi menu to select the default audio output device
#
# Dependencies:
#   System:     pacmd, pactl
#   pip:        rofi-menu

import subprocess
import re
import rofi_menu

cmd_listsinks = ["pacmd", "list-sinks"]
re_header = ".+index:.+[0-9]+$"
re_productname = "device\.product\.name"
re_sinkname = "name:"


class Menu(rofi_menu.Menu):
    prompt = "Default output sink"
    items = []

    def addSinks(self, sinks):
        for sink in sinks:
            if (sink.isOutput):
                self.items.append(rofi_menu.ShellItem(
                    str(sink), "pacmd set-default-sink " + sink.index))


class Sink:
    def __init__(self):
        self.index = -1
        self.name = "NULL"
        self.isDefault = False
        self.isOutput = False

    def __repr__(self, showIndex=False):
        result = ("▸ " if (self.isDefault) else "  ")
        if (showIndex):
            result += str(self.index) + ": "
        return result + self.name


def fetchSinks(printEntries=False):
    sinks = []

    info = str(subprocess.check_output(cmd_listsinks)
               ).replace("\\t", "").split("\\n")

    sink = None
    for line in info:
        # New sink entry
        if (re.match(re_header, line)):
            sink = Sink()
            sinks.append(sink)

            headers = line.replace(" ", "").split(":")

            sink.isDefault = headers[0].startswith('*')
            sink.index = headers[1]

        if (sink == None):
            continue

        if (re.match(re_productname, line)):
            sink.name = line.split("\"")[1]
        if (re.match(re_sinkname, line)):
            sink.isOutput = "alsa_output" in line

    if (printEntries):
        print("Sinks:")
        for sink in sinks:
            if (sink.isOutput):
                print(sink, True)

    return sinks


if __name__ == "__main__":
    menu = Menu()
    menu.addSinks(fetchSinks())
    rofi_menu.run(menu, rofi_version="1.6")
