#!/bin/python

# Creates a rofi menu to select the current screen layout
#
# Dependencies:
#   System:     autorandr (with xrandr)

import subprocess
import re
import rofi_menu

class Menu(rofi_menu.Menu):
    prompt = "Display layout"
    items = []

    def addEntries(self, entries):
        for entry in entries:
            if (entry.isVisible):
                self.items.append(rofi_menu.ShellItem(
                    str(entry), "autorandr --load " + entry.name))

class Entry:
    def __init__(self):
        self.name = "NULL"
        self.isDefault = False
        self.isActive = False
        self.isVisible = True

    def __repr__(self, showIndex=False):
        result = ("▸ " if (self.isActive) else "  ")
        if (showIndex):
            result += str(self.index) + ": "
        return result + self.name

def fetchEntries(printEntries=False):
    entries = []
    entry = None

    # fetch currently available config(s)
    detected = subprocess.check_output(["autorandr", "--detected"]).decode('utf-8').split("\n")[:-1]

    for line in detected:
        # New entry
        entry = Entry()
        entries.append(entry)
        
        entry.IsVisible = True
        entry.isActive = False
        entry.name = line
        
    # fetch currently active config(s)
    current = subprocess.check_output(["autorandr", "--current"]).decode('utf-8').split("\n")[:-1]

    for line in current:
        for detectedEntry in entries:
            if detectedEntry.name == line:
                detectedEntry.isActive = True

    if (printEntries):
        print("Entries:")
        for entry in entries:
            print(entry)

    return entries


if __name__ == "__main__":
    menu = Menu()
    menu.addEntries(fetchEntries())
    rofi_menu.run(menu, rofi_version="1.6")
