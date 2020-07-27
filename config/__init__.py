"""Contains config variables.

Switches config details based on environment or platform. To set it up, make a copy of template.py, edit it and name
it production.py

Check init for more details."""

import os
import platform

# TODO: Still a lot work to do...

# Detect if deployed on Heroku. NOTE: This is not currently in use.
HEROKU_DEPLOYED = bool("DYNO" in os.environ)

# Loads dev config on Windows by default.

if "Windows" in platform.system():
    os.environ["PYTHONASYNCIODEBUG"] = "1"
    try:
        from config.development import *
    except ImportError:
        try:
            from config.production import *
        except ImportError:
            raise Exception("Please set up the config module properly.")
else:
    try:
        from config.production import *
    except ImportError:
        raise Exception("Please set up the config module properly.")
