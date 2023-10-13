'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: MIT
'''

import os
import shutil

def print_action(action,details=[]):
    banner = "="*len(action) 
    print(banner)
    print(action)
    print(banner)
    for detail in details:
        print("\t{}".format(detail))
    print()


def create_directory(directory, remove=True):

    directory = os.path.abspath(directory)
    
    if (remove):
        try:
            print_action("Removing: {}".format(directory))
            shutil.rmtree(directory,ignore_errors=True)
        except Exception as error:
            print(error)

    print_action("Creating: {}".format(directory))
    os.makedirs(directory,exist_ok=True)
