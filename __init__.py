import os
import sys

sys.path.append(
    os.getenv("HOME", "/home/" + os.getenv("USER", "neg")) +  "/.config/i3/lib"
)

