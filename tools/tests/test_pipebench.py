#!/bin/python3

import shlex
import shutil
import subprocess
import threading 
import signal
import os
import sys
import yaml
import glob
import pytest
import json

timeout_sec = 60

test_workspace = "/home/test_workspace"     

def pytest_report_header(config):
    return "test download command of pipebench"


def run_cmd(cmd_str):
    #exec_cmd = "timeout " + str(timeout_sec) + " " + cmd_str 
    proc = subprocess.Popen(shlex.split(cmd_str), stderr=subprocess.PIPE, shell=False) 
    stderr = proc.communicate()
    exitcode = proc.returncode
    return exitcode, stderr


# todo validate against measurement schema        
def check_measurement(pipeline, measurement, scenario="disk"):
    pipeline_root = os.path.join(test_workspace, pipeline)
    results_path = os.path.join(pipeline_root,
                                "measurements",
                                measurement,
                                "dlstreamer",
                                "run-0000",
                                "result.json")
    assert(os.path.isfile(results_path))
    with open(results_path) as results_file:
        result = json.load(results_file)
        assert(measurement in result)
        
def check_download(pipeline):
    pipeline_root = os.path.join(test_workspace, pipeline)
    subfolders = []
    list_files = [fname for fname in os.listdir(pipeline_root) if fname.endswith("list.yml")]
    media_list = [fname for fname in list_files if fname.endswith("media.list.yml")]
    model_list = [fname for fname in list_files if fname.endswith("models.list.yml")]
    runners = [fname for fname in os.listdir(pipeline_root)
               if fname.endswith("runner-settings.yml")]
    if media_list:
        subfolders.append("media")
    if model_list:
        subfolders.append("models")
    if runners:
        subfolders.append("runners")
    for subfolder in subfolders:
        assert(os.path.isdir(os.path.join(pipeline_root, subfolder)))           

@pytest.mark.timeout(600)
def test_download(pipeline):
    test_cmd = "pipebench download {} --force --workspace {}".format(pipeline, test_workspace)
    
    exitcode, err = run_cmd(test_cmd);
    print ("command exit code = %d" % exitcode)
    if(err[0] != None):
        print ("stderr: ") 
        print(err)     
    if(exitcode == 124):
        pytest.fail("test was terminated after {} seconds".format(timeout_sec));
        assert False
    elif(exitcode == 0):
        assert True
    elif(exitcode != 0):
        assert False
    # if no error codes then check 
    check_download(pipeline)

@pytest.mark.timeout(600)
def test_throughput(pipeline):
    test_cmd = "pipebench  run {} --workspace {}".format(pipeline, test_workspace)
    
    exitcode, err = run_cmd(test_cmd);
    print ("command exit code = %d" % exitcode)
    if(err[0] != None):
        print ("stderr: ") 
        print(err)     
    if(exitcode == 124):
        pytest.fail("test was terminated after {} seconds".format(timeout_sec));
        assert False
    elif(exitcode == 0):
        assert True
    elif(exitcode != 0):
        assert False
    # if no error codes then check 
    check_measurement(pipeline,"throughput")


@pytest.mark.timeout(600)
def test_density(pipeline):
    test_cmd = "pipebench run {} --measure density --workspace {} --max-streams 8".format(pipeline, test_workspace)
    
    exitcode, err = run_cmd(test_cmd);
    print ("command exit code = %d" % exitcode)
    if(err[0] != None):
        print ("stderr: ") 
        print(err)     
    if(exitcode == 124):
        pytest.fail("test was terminated after {} seconds".format(timeout_sec));
        assert False
    elif(exitcode == 0):
        assert True
    elif(exitcode != 0):
        assert False
    # if no error codes then check 
    check_measurement(pipeline,"density")


