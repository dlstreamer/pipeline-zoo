'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import shutil
import sys
import time
import threading

def print_action(action,details=[]):
    banner = "="*len(action) 
    print(banner)
    print(action)
    print(banner)
    for detail in details:
        print("\t{}".format(detail))
    print()


def create_directory(directory, remove=True):

    if (remove):
        try:
            shutil.rmtree(directory,ignore_errors=True)
        except Exception as error:
            print(error)

    os.makedirs(directory,exist_ok=True)

class Spinner:
    busy = False
    delay = 0.1

    cursors = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    @staticmethod
    def spinning_cursor():
        while 1: 
            for cursor in Spinner.cursors: yield cursor

    def __init__(self, text="", delay=None):
        self.label = text + ": "
        self.CLEAR_LINE = "\b" * (len(self.label) + 1)
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): self.delay = delay

    def start(self):
        if hasattr(sys.stdout, "isatty") and not sys.stdout.isatty():
            return
        self.busy = True
        threading.Thread(target=self.spinner_task).start()
    
    def stop(self):
        self.busy = False
        time.sleep(self.delay)

    def __enter__(self):
        self.start()

    def __exit__(self, exception, value, tb):
        self.stop()

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(self.label + next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write(self.CLEAR_LINE)
            sys.stdout.flush()
    
    
