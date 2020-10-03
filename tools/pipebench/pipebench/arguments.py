'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
import os
import argparse
import json
import distutils.util
from schema.documents import WorkloadConfig

package_name = os.path.split(os.path.dirname(__file__))[-1]

    
def parse_args(args=None,program_name=package_name):

    parser = argparse.ArgumentParser(prog=program_name,fromfile_prefix_chars='@',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--workspace",
                        action="store",
                        dest="workspace_root",
                        required=False,
                        default="workspace")

    parser.add_argument("--override",
                        action="append",
                        nargs=2,
                        required=False,
                        dest="overrides",
                        default=[])

    
    parser.add_argument("--workload", action="store", dest="workload",required=True)

    parser.add_argument("--runner", action="store", dest="runner",required=False, default="mockrun")

    parser.add_argument("--force", required=False, dest="force",action="store_true", default=False)

    parser.add_argument("--dry-run", action="store_true", dest="dry_run",default=False)

    parser.add_argument("--no-redirect", action="store_false", dest="redirect",default=True)

    parser.add_argument("commands", choices=["download","prepare","run","report", "view"],default=["view"],nargs='+')

    
    if (isinstance(args, dict)):
        args = ["--{}={}".format(key, value)
                for key, value in args.items() if value]


    return parser.parse_args(args), parser

    
