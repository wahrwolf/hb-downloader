#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess


def test_help():
    # Check that the script runs and displays the help text without errors
    subprocess.check_output(["python3", "hb-downloader.py", "-h"])

    # Check the same with basic actions
    actions = ["download", "list"]
    for a in actions:
        subprocess.check_output(["python3", "hb-downloader.py", a, "-h"])
