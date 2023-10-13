#!/usr/bin/env python3
'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: MIT
'''

import os, traceback
import atexit
import psutil
import yaml
import json
from tasks.decode_vpp import DecodeVPP
from tasks.object_detection import ObjectDetection
from tasks.object_classification import ObjectClassification
from tasks.object_tracking import ObjectTracking
from tasks.object_detection_multi import ObjectDetectionMulti
from tasks.task import Task
import sys
import signal

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

def cleanup(_signal_unused=None,_frame_unused_=None):
    children = psutil.Process().children(recursive=True)
    for child in children:
        print("Terminating: {}".format(child),flush=True)
        child.terminate()
    gone, alive = psutil.wait_procs(children,timeout=3)
    for child in alive:
        print("Killing: {}".format(child),flush=True)
        child.kill()        
    
if __name__ == '__main__':
    parser = None
    try:
        os.setpgrp()
        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)
        atexit.register(cleanup)

        args, parser = parse_args(program_name=package_name)
        print_args(args)

        args.piperun_config_path = args.piperun_config
        args.piperun_config = load_document(args.piperun_config)

        if args.systeminfo:
            args.systeminfo = load_document(args.systeminfo)

        task = Task.create_task(args.piperun_config,args)

        task.start()
        task.join()

        if (task.completed):
            sys.exit(task.completed.returncode)
        else:
            sys.exit(-1)
    except(KeyboardInterrupt, SystemExit):
        pass
    
    except Exception as error:
        print("\n\n")
        traceback.print_tb(error.__traceback__)
        print("\n\n")
        if (parser):
            parser.error("\n\n{}\n\n".format(error))
        else:
            print("\n\n{}\n\n".format(error))
    
