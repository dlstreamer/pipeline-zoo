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

def _get_common_parser():
    common_parser = argparse.ArgumentParser(add_help=False,
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    common_parser.add_argument("-v",
                               "--verbose",
                               action="count",
                               dest="verbose_level",
                               required=False,
                               help="Verbosity level",
                               default=0)
   
    common_parser.add_argument("--workspace",
                               action="store",
                               dest="workspace_root",
                               required=False,
                               help="Workspace directory",
                               default=".")
    return common_parser

def _add_measurement_settings(parser):
    measurement_settings = parser.add_argument_group("Measurement Settings",argument_default=argparse.SUPPRESS)
    measurement_settings.add_argument("--media",
                        help="media name as listed in media.list.yml"\
                        ", path to media directory, or path to media file").complete=shtab.FILE
    measurement_settings.add_argument("--warm-up",
                                      type=int,
                                      help="Number of samples to discard before reporting fps (default: 2)")
    measurement_settings.add_argument("--duration",
                                      type=int,
                                      help="Number of seconds for run (default: 60)")

    numactl = measurement_settings.add_mutually_exclusive_group()

    numactl.add_argument("--numactl",
                         action="store_true",
                         help="Places each runner process on a numa node."
                         " Cycles between numa nodes so runner processes"
                         " are distributed evenly accross available nodes. (default: True)")
    numactl.add_argument("--no-numactl",
                         action="store_false",
                         dest="numactl",
                         help="Disable numactrl and use OS default placement")

    measurement_settings.add_argument("--streams",
                                      type=int,
                                      help="Number of concurrent media streams. If set to 0 (AUTO) "
                                      "pipebench will iterate until a maximum stream density "
                                      "is calculated based on the target fps and target "
                                      "condition (default: 1)")

    measurement_settings.add_argument("--target-fps",
                                      type=int,
                                      help="Target FPS (default: 30)")

    measurement_settings.add_argument("--target-condition",
                                      choices=["stream", "average", "total"],
                                      help="Condition for selecting maximum during search."
                                      " stream selects the maximum stream density with the requirement that each individual stream meets the TARGET_FPS."
                                      " average selects the maximum stream density with the requirement that the average FPS over all streams meets the TARGET_FPS."
                                      " total maximizes the total FPS (default: total)")  

    measurement_settings.add_argument("--sample-size",
                                      type=int,
                                      help="Number of frames to use in updating FPS."
                                      "Avg FPS will be recalculated every sample period. (default: 30)")

    measurement_settings.add_argument("--target-range",
                                      help="Min and max tolerance for target-fps as list [min,max]."
                                      " [0] indicates target fps must be met (TARGET_FPS <= FPS)."
                                      " [0.2] indicates (TARGET_FPS - 0.2) <= FPS. [0.2,0.2]"
                                      " indicates (TARGET_FPS - 0.2) <= FPS <= (TARGET_FPS + 0.2) (default: [0.2])")

    measurement_settings.add_argument("--starting-streams",
                                      type=int,
                                      help="Number of concurrent media streams to start with"
                                      " when iterating to find maximum stream density."
                                      " If set to 0 (AUTO) starting streams will be calculated"
                                      " based on single process throughput / TARGET_FPS."
                                      " Only applies when --streams is set to 0 (AUTO) (default: 0)")

    measurement_settings.add_argument("--streams-per-process",
                                      type=int,
                                      help="Number of media streams handled by each pipeline runner process."
                                      " If set to 0 (NONE) all streams will be sent to a single runner"
                                      " process. The number of pipeline runner processes launched in each"
                                      " iteration will be MIN( (NUMBER_OF_STREAMS / STREAMS_PER_PROCESS),"
                                      " MAX_PROCESSES) (default: 1)")

    measurement_settings.add_argument("--max-processes",
                                      type=int,
                                      help="Maximum number of pipeline runner processes to launch."
                                      " If set to 0 (NO LIMIT) there is no limit and the "
                                      " number of processes is determined by NUMBER_OF_STREAMS /"
                                      " STREAMS_PER_PROCESS. (default: 0)")

    measurement_settings.add_argument("--max-streams",
                                      type=int,
                                      help="Maximum number of concurrent media streams when iterating."
                                      " If set to 0 (NO LIMIT) no limit is applied. Only applies "
                                      " when --streams is set to 0 (AUTO). (default: 0)")

    measurement_settings.add_argument("--max-iterations",
                                      type=int,
                                      help="Maximum number of iterations to perform when"
                                      " finding maximum stream density."
                                      " If set to 0 (NO LIMIT) no limit is applied."
                                      " Only applies when --streams is set to 0 (AUTO) (default: 0)")
    measurement_settings.add_argument("--min-streams",
                                      type=int,
                                      help="Minimum number of media streams when iterating."
                                      " Must be less than or equal to--starting-streams (default: 1)")

    measurement_settings.add_argument("--search-method",
                                      choices=["linear","binary"],
                                      help="Method for finding maximum stream density."
                                      "Note: binary is experimental at this time. (default: linear)")

    measurement_settings.add_argument("--generate-reference",
                                      action="store_true",
                                      help="Generate reference data when preparing workload."
                                      "Note: Reference data is not needed for performance measurements"
                                      " and increases workload preparation time significantly. (default: False)")

    measurement_settings.add_argument("--save-pipeline-output",
                                      action="store_true",
                                      help="Save pipeline output"
                                      "Note: Pipeline output is not needed for performance measurements"
                                      " and can impact FPS (default: False)")


def _get_parser(program_name="pipebench"):
    parser = argparse.ArgumentParser(prog=program_name,fromfile_prefix_chars='@',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    common_parser = _get_common_parser()

    subparsers = parser.add_subparsers(dest="command",
                                       metavar="list, download, run",
                                       title="commands")
    subparsers.required = True

    list_parser = subparsers.add_parser("list",
                                        parents=[common_parser],
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    list_parser.set_defaults(command=pipebench.commands.list_pipelines)

    common_parser.add_argument("pipeline",
                               metavar="pipeline",
                               choices=list_pipelines()[0])

    download_parser = subparsers.add_parser("download", parents=[common_parser],
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    download_parser.set_defaults(command=pipebench.commands.download)

    download_parser.add_argument("--force",
                                 required=False,
                                 dest="force",
                                 action="store_true",
                                 help="Force download of existing pipeline",
                                 default=False)

    download_parser.add_argument("--silent",
                                 required=False,
                                 dest="silent",
                                 action="store_true",
                                 help="Disable output from download",
                                 default=False)

    run_parser = subparsers.add_parser("run",
                                       parents=[common_parser],
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    run_parser.add_argument("--measure",
                            required=False,
                            dest="measurement",
                            default="throughput",
                            help="Measurement to perform. Used as selector "\
                            "for measurement and runner settings.")

    run_parser.add_argument("--runner",
                            required=False,
                            default="dlstreamer",
                            help="Pipeline runner implementation")

    run_parser.add_argument("--runner-settings",
                            required=False,
                            help="Pipeline runner settings. "\
                            "If not specified runner settings "\
                            "will be selected based on measurement and platform.")

    run_parser.add_argument("--save-runner-settings",
                            required=False,
                            default=None,
                            help="Save pipeline runner settings with overrides.")
    
    run_parser.add_argument("--platform",
                            required=False,
                            help="Platform name. Used as selector "\
                            "for measurment and runner settings.")
    
    run_parser.add_argument("--save-measurement-settings",
                            required=False,
                            default=None,
                            help="Name for saving measurement settings")
    
    run_parser.add_argument("--runner-override",
                            action="append",
                            nargs=2,
                            required=False,
                            dest="runner_overrides",
                            help="Override settings for runner",
                            default=[])
    
    run_parser.add_argument("--measurement-settings",
                            action="store",
                            required=False,
                            help="Measurement settings to load",
                            default=None).complete=shtab.FILE

    run_parser.add_argument("--measurement-directory",
                            required=False,
                            help="Directory to store measurements",
                            default=None).complete=shtab.DIRECTORY

    run_parser.add_argument("--force",
                            required=False,
                            dest="force",
                            action="store_true",
                            help="Force clearing of previous results",
                            default=False)
    
    #run_parser.add_argument("--override",
    #                        action="append",
    #                        nargs=2,
    #                        required=False,
    #                        dest="overrides",
    #                        default=[])

    _add_measurement_settings(run_parser)
    run_parser.set_defaults(command=pipebench.commands.run)
          
    return parser
    
def parse_args(args=None,program_name="pipebench"):

    parser = _get_parser()
    
    if (isinstance(args, dict)):
        args = ["--{}={}".format(key, value)
                for key, value in args.items() if value]
        
    return parser.parse_args(args), parser

    
