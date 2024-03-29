#!/usr/bin/env python3
'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: MIT
'''

import os, traceback
from pipebench.arguments import parse_args
from pipebench.arguments import list_pipelines
from pipebench.arguments import find_zoo_root
from pipebench.schema.documents import load_schemas
from pipebench.schema.documents import load_tasks
from pipebench.tasks.object_detection import ObjectDetection
from pipebench.tasks.object_classification import ObjectClassification
from pipebench.tasks.object_tracking import ObjectTracking
from pipebench.tasks.decode_vpp import DecodeVPP
from pipebench.tasks.object_detection_multi import ObjectDetectionMulti
from util import print_action
import logging
import shlex
import shutil
import subprocess
import atexit
import signal
import psutil

def print_args(args):
    if args.verbose_level > 0:
        heading = "Arguments for {}".format("pipebench")
        banner = "="*len(heading) 
        print(banner)
        print(heading)
        print(banner)
        for arg in vars(args):
            print ("\t{} == {}".format(arg, getattr(args, arg)))
        print()

def initialize(parser, args):
    args.workspace_root = os.path.abspath(args.workspace_root)

    args.zoo_root = find_zoo_root()

    args.parser = parser

    if (not args.zoo_root):
        parser.error("Can't find Zoo!")
    
    load_schemas(args)
        
    load_tasks(args)

def cleanup():
    children = psutil.Process().children(recursive=True)
    for child in children:
        print("Terminating: {}".format(child))
        child.terminate()
    gone, alive = psutil.wait_procs(children,timeout=3)
    for child in alive:
        print("Killing: {}".format(child))
        child.kill()        

if __name__ == '__main__':
    parser = None
    try:
        os.setpgrp()
        atexit.register(cleanup)
        args, parser = parse_args(program_name="pipe")

        print_args(args)

        initialize(parser, args)
        args.pipelines = list_pipelines()
        args.command(args)
    except(KeyboardInterrupt, SystemExit):
        pass
    
    except Exception as error:
        print("\n\n")
        traceback.print_tb(error.__traceback__)
        print("\n\n")
        if (parser):
            parser.error("\n\n\n{}\n\n\n".format(error))
        else:
            print("\n\n\n{}\n\n\n".format(error))
        
