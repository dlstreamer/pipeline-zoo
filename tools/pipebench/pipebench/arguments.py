'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
import os
import argparse
import json
import distutils.util
import shtab
import pipebench.commands

def find_zoo_root():
    path = os.path.realpath(__file__)
    while (path and not os.path.basename(path)=='tools'):
        path = os.path.dirname(path)
    return os.path.dirname(path)

def list_runners():
    runners_root = os.path.join(find_zoo_root(),"runners")
    for root, directories, files in os.walk(runners_root):
        return directories
    
def list_pipelines():
    pipelines_root = os.path.join(find_zoo_root(),"pipelines")
    pipelines = []
    pipeline_paths = []
    for root, directories, files in os.walk(pipelines_root):
        for path in files:
            if (path.endswith(".pipeline.yml")):
                pipelines.append(path.replace(".pipeline.yml",""))
                pipeline_paths.append(os.path.join(root,path))
    return pipelines, pipeline_paths    

def _get_parser_shtab():
    parser = _get_parser()

    for command in parser._get_positional_actions():
        for cmd, subparser in command.choices.items():
            for option in subparser._get_optional_actions():
                if (option.choices):
                    option_strings = []
                    option_string = option.option_strings[0]
                    for choice in option.choices:
                        option_strings.append("{}={}".format(option_string,choice))
                    option.option_strings = option_strings
                
    return parser

def _get_parser(program_name="pipebench"):
    parser = argparse.ArgumentParser(prog=program_name,fromfile_prefix_chars='@',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)


    
    parser.add_argument("--workspace",
                        action="store",
                        dest="workspace_root",
                        required=False,
                        default=".")
    
    subparsers = parser.add_subparsers(dest="command",
                                       metavar="download, measure, run, list",
                                       title="commands")
    subparsers.required = True

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(command=pipebench.commands.list_pipelines)
    
    download_parser = subparsers.add_parser("download")

    download_parser.add_argument("pipeline",
                                 metavar="pipeline",
                                 choices=list_pipelines()[0])
    download_parser.set_defaults(command=pipebench.commands.download)

    download_parser.add_argument("--force", required=False, dest="force",action="store_true", default=False)
    download_parser.add_argument("--silent", required=False, dest="silent",action="store_true", default=False)
    download_parser.add_argument("-v", required=False, dest="verbose",action="count", default=0)

    measure_parser = subparsers.add_parser("measure")
    measure_parser.add_argument("pipeline",
                                metavar="pipeline",
                                choices=list_pipelines()[0])
    
    measure_parser.add_argument("--override",
                                 action="append",
                                 nargs=2,
                                 required=False,
                                 dest="overrides",
                                 default=[])

    measure_parser.add_argument("--platform",
                                required=False,
                                dest="platform",
                                default="")

    measure_parser.add_argument("--runner-config",
                                required=False,
                                dest="runner_config",
                                default="")

    measure_parser.add_argument("--save-workload",
                                required=False,
                                dest="save_workload",
                                default=None)
    
    measure_parser.add_argument("--save-runner-config",
                                required=False,
                                dest="save_runner_config",
                                default=None)

    measure_parser.add_argument("--runner-override",
                                 action="append",
                                 nargs=2,
                                 required=False,
                                 dest="runner_overrides",
                                 default=[])

    measure_parser.add_argument("--runner",
                                required=False,
                                default="dlstreamer",
                                choices=list_runners())

    measure_parser.add_argument("--workload",
                                action="store",
                                dest="workload",
                                required=False,
                                default=None)

    measure_parser.add_argument("--save-pipeline-output",
                                action="store_true",
                                required=False,
                                default=False)

    measure_parser.add_argument("--measurement-directory",
                                required=False,
                                default="")

    measure_parser.add_argument("--generate-reference",
                                required=False,
                                action="store_true",
                                default=False)

    measure_parser.add_argument("--force", required=False, dest="force",action="store_true", default=False)

    
    measure_parser.set_defaults(command=pipebench.commands.measure)
    measure_parser.add_argument("--add-timestamp", action="store_true", dest="add_timestamp",default=False)
    measure_parser.add_argument("--no-redirect", action="store_false", dest="redirect",default=True)
    measure_parser.add_argument("--no-prepare-timeout", action="store_false", dest="prepare_timeout",default=True)

    measurement = measure_parser.add_mutually_exclusive_group()
    
    measurement.add_argument("--density", action="store_true", dest="density",default=False)
    measurement.add_argument("--throughput", action="store_true", dest="throughput",default=False)    
        
    
    return parser
    
def parse_args(args=None,program_name="pipebench"):

    parser = _get_parser()
    
    if (isinstance(args, dict)):
        args = ["--{}={}".format(key, value)
                for key, value in args.items() if value]
        
    return parser.parse_args(args), parser

    
