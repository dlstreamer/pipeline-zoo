'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import shutil
import threading

print_lock = threading.Lock()

def print_action(action,details=[]):
    message = []
    banner = "="*len(action)
    message.append(banner)
    message.append(action)    
    for detail in details:
        message.append("\t{}".format(detail))
    message.append(banner)
    message.append("")
    with(print_lock):
        print("\n".join(message),flush=True)


def create_directory(directory, remove=True,verbose_level=0):

    directory = os.path.abspath(directory)
    
    if (remove):
        try:
            shutil.rmtree(directory,ignore_errors=True)
        except Exception as error:
            print(error)

    try:
        os.makedirs(directory,exist_ok=False)
        if verbose_level > 2:
            print_action("Creating: {}".format(directory))
    except FileExistsError as error:
        print_action("Reusing: {}".format(directory))
