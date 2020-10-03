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

    handler = handler_map[args.handler_type](args)
    
    handler.prepare()

    
