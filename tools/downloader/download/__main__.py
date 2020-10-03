#!/usr/bin/env python3
'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import sys
from arguments import parse_args
import handlers
from handlers import load_document
from arguments import find_pipeline_root

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


handler_map = {handler_class.__name__.lower():handler_class for handler_class in handlers.Handler.__subclasses__()}

if __name__ == '__main__':

    args = parse_args(program_name=package_name)
    print_args(args)

    pipelines = []

    for pipeline in args.pipelines:
        if (os.path.isfile(pipeline)):
            pipeline_list = load_document(pipeline)
            for pipeline_item in pipeline_list:
                pipelines.append(pipeline_item)
        else:
            pipelines.append(pipeline)

    for pipeline in pipelines:

        pipeline_root = find_pipeline_root(args,pipeline)
        
        if (os.path.isdir(pipeline)):
            pipeline = os.path.basename(pipeline)
        
        if (not pipeline_root):
            print("Can't find pipeline root for: {}, Skipping".format(pipeline))
            continue

        if ('pipeline' in args.item_types):
            args.item_types.remove('pipeline')
            args.item_types.insert(0,'pipeline')

        for item_type in args.item_types:
            handler = handler_map[item_type](args)
            item_list = getattr(args,"{}_list".format(item_type),None)
            item = getattr(args,"{}_item".format(item_type),None)
            handler.download(pipeline,
                             pipeline_root,
                             item,
                             item_list)
            
    

    
