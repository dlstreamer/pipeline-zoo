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


def parse_args(args=None,program_name=package_name):

    parser = argparse.ArgumentParser(description="Prepare media and pipelines for upload to Pipeline Zoo.")
    parser.add_argument("-t", "--type", choices=handler_choices,required=True,dest="handler_type")
    parser.add_argument("-d", "--destination", required=False,dest="destination",default=".")
    parser.add_argument("source")
    

    if (isinstance(args, dict)):
        args = ["--{}={}".format(key, value)
                for key, value in args.items() if value]
        
    args = parser.parse_args(args)
    args.source = os.path.abspath(args.source)
    args.destination = os.path.abspath(args.destination)
    
    return args

    
