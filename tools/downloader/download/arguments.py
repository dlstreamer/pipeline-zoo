'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
import os
import argparse
import json
import distutils.util
import handlers

package_name = os.path.split(os.path.dirname(__file__))[-1]

handler_choices = [x.__name__.lower() for x  in handlers.Handler.__subclasses__()]

def find_zoo_root():
    path = os.path.abspath(__file__)
    while (path and not os.path.basename(path)=='tools'):
        path = os.path.dirname(path)
    return os.path.dirname(path)

def find_pipeline_root(args, pipeline):
    pipelines_root = os.path.join(args.zoo_root,"pipelines")
    
    for root, directories, files in os.walk(pipelines_root):
        if (pipeline in directories):
            return os.path.abspath(os.path.join(root,pipeline))

    default_path = os.path.abspath(pipeline)
    if (os.path.isdir(default_path)):
        return default_path
    
    return None


def parse_args(args=None,program_name=package_name):

    parser = argparse.ArgumentParser(description="Download media, pipelines and models from Pipeline Zoo.")
    parser.add_argument("-t", "--type", choices=handler_choices,
                        default=handler_choices,
                        required=False,
                        dest="item_types",
                        nargs='+')

    parser.add_argument("-d", "--destination", required=False,dest="destination",default=".")

    for handler in handler_choices:
        if (not handler == "pipeline"):
            parser.add_argument("--{0}-list".format(handler), required=False,
                                dest="{0}_list".format(handler))

            parser.add_argument("--{0}-item".format(handler), required=False,
                                dest="{0}_item".format(handler))    

    parser.add_argument("--force", required=False, dest="force",action="store_true", default=False)

    parser.add_argument("--media-root", required=False, dest="media_root",
                        default="https://gitlab.devtools.intel.com/media-analytics-pipeline-zoo/media")

    parser.add_argument("pipelines",nargs='+')
    

    if (isinstance(args, dict)):
        args = ["--{}={}".format(key, value)
                for key, value in args.items() if value]
        
    args = parser.parse_args(args)
    args.destination = os.path.abspath(args.destination)
    args.zoo_root = find_zoo_root()
    args.runners_root = os.path.join(args.zoo_root,"runners")
    
    return args

    
