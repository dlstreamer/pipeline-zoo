#!/usr/bin/env python3
'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os

from pipebench.arguments import parse_args
from pipebench.schema.documents import load_schemas
from pipebench.schema.documents import WorkloadConfig
from pipebench.schema.documents import load_tasks
from pipebench.tasks.task import Task
from pipebench.tasks.object_detection import ObjectDetection
from pipebench.commands import command_map
from util import print_action
import shlex
import shutil
import subprocess

package_name = os.path.basename(os.path.dirname(__file__))

def print_args(args):
    heading = "Arguments for {}".format(package_name)
    banner = "="*len(heading) 
    print(banner)
    print(heading)
    print(banner)
    for arg in vars(args):
        print ("\t{} == {}".format(arg, getattr(args, arg)))
    print()


def find_zoo_root():
    path = os.path.abspath(__file__)
    while (path and not os.path.basename(path)=='tools'):
        path = os.path.dirname(path)
    return os.path.dirname(path)

def load_workload_config(parser, args):
    args.workspace_root = os.path.abspath(args.workspace_root)

    args.zoo_root = find_zoo_root()

    if (not args.zoo_root):
        parser.error("Can't find Zoo!")
    
    load_schemas(args)
        
    load_tasks(args)

    try:
        workload = WorkloadConfig(args.workload, args)
        workload_name = os.path.basename(args.workload)
        workload_name = workload_name.split('.')[0]

        args.workload_name = workload_name
        args.workload_root = os.path.join(args.
                                          workspace_root,
                                          workload.pipeline,
                                          "workloads",
                                          workload_name)

        
        
        return workload
    except Exception as error:
        parser.error("Invalid workload: {}, error: {}".format(args.workload,error))

    return None

def run_commands(task, workload, args):
    command_order = ["view","prepare","run","report"]
    for command in command_order:
        if command in args.commands:
            print_action(command)
            command_map[command](task, workload, args)
    
if __name__ == '__main__':

    args, parser = parse_args(program_name=package_name)
    print_args(args)
    workload = load_workload_config(parser, args)

    if ( ("run" in args.commands) and (not args.runner)):
        parser.error("Run command given but runner not specified")

    if ("download" in args.commands):
        command_map["download"](None,workload,args)

    

    task = Task.create_task(workload, args)

    run_commands(task, workload, args)
    
  
