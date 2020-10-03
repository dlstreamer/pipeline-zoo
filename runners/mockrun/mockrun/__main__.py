#!/usr/bin/env python3
'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import yaml
import json
from tasks.task import Task

from arguments import parse_args

package_name = os.path.basename(os.path.dirname(__file__))

def load_document(document_path):
    document = None
    with open(document_path) as document_file:
        if (document_path.endswith('.yml')):
            document = yaml.full_load(document_file)
        elif (document_path.endswith('.json')):
            document = json.load(document_file)
    return document


def print_args(args):
    heading = "Arguments for {}".format(package_name)
    banner = "="*len(heading) 
    print(banner)
    print(heading)
    print(banner)
    for arg in vars(args):
        print ("\t{} == {}".format(arg, getattr(args, arg)))
    print()


    
if __name__ == '__main__':

    args, parser = parse_args(program_name=package_name)
    print_args(args)
    

    args.piperun_config = load_document(args.piperun_config)

    task = Task.create_task(args.piperun_config,args)

    task.start()
    task.join()
    print("hello")
    
#    load_reference(args)
    
    
