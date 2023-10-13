#!/usr/bin/env python3
'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import sys

from systeminfo import collect_configuration
from systeminfo import generate_json
from arguments import parse_args

print(sys.path)

print(__name__)
print(__package__)

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

if __name__ == '__main__':

    args = parse_args(program_name=package_name)
    print_args(args)
    info = collect_configuration(args)

    # pylint: disable=no-member
    if args.json:
        generate_json(info, args.json)
    # pylint: enable=no-member
