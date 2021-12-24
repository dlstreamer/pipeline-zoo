'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
import os
import argparse
import json
import distutils.util

package_name = os.path.split(os.path.dirname(__file__))[-1]

def parse_args(args=None,program_name=package_name):

    parser = argparse.ArgumentParser(description="Display system info of linux machine.")
    parser.add_argument("-p",  "--prefix",     default="",    help="Prefix for specific commands (clinfo)")
    parser.add_argument("-c",  "--config",     default="",    help="Path to config")
    parser.add_argument("-b",  "--bitstreams", default="",    help="Path to bitstreams")
    parser.add_argument("-j",  "--job",        default="",    help="Job name")
    parser.add_argument("-m",  "--modelzoo",   default="",    help="Path to model-zoo code")
    parser.add_argument("--open-model-zoo-repo",   default="",    help="Path to open model zoo code repository")
    parser.add_argument("-js", "--json",                      help="JSON output file with system configuration", default="systeminfo.json")
    parser.add_argument("-f",  "--fp11",       default=False, help="Use fp11", required=False)
    parser.add_argument("--openvino",                         help="OpenVINO path")

    if (isinstance(args, dict)):
        args = ["--{}={}".format(key, value)
                for key, value in args.items() if value]
        
    args = parser.parse_args(args)

    if not args.openvino:
        args.openvino = os.environ.get("INTEL_OPENVINO_DIR", "/opt/intel/openvino")

    return args

    
