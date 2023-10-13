'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: MIT
'''
import os
import argparse
import json
import distutils.util

package_name = os.path.split(os.path.dirname(__file__))[-1]

    
def parse_args(args=None,program_name=package_name):

    parser = argparse.ArgumentParser(prog=program_name,fromfile_prefix_chars='@',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    
    parser.add_argument("--systeminfo", action="store", dest="systeminfo",required=False)
    
    parser.add_argument("piperun_config", metavar="piperun config", action="store", help="piperun configuration file (.piperun.yml)")

    
    if (isinstance(args, dict)):
        args = ["--{}={}".format(key, value)
                for key, value in args.items() if value]


    return parser.parse_args(args), parser

    
