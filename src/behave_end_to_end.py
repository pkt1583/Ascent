import os
import sys

from behave.__main__ import main as behave_main

# This is purely for debugging on local. Please don't add any logic here
if __name__ == "__main__":
    os.environ.setdefault("IS_RUNNING_END_TO_END", "true")
    sys.exit(behave_main("tests/end-to-end-bdd"))
