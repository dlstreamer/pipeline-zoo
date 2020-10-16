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

pipelines = ["od-h264-mbnetssd"]
#             "od-h264-yolov3"]

timeout_sec = 60

test_workspace = "/home/test_workspace"     

def pytest_report_header(config):
    return "test downalod command of pipebench"


def run_cmd(cmd_str):
    #exec_cmd = "timeout " + str(timeout_sec) + " " + cmd_str 
    proc = subprocess.Popen(shlex.split(cmd_str), stderr=subprocess.PIPE, shell=False) 
    stderr = proc.communicate()
    exitcode = proc.returncode
    return exitcode, stderr


# todo validate against measurement schema        
def check_measurement(pipeline, measurement):
    pipeline_root = os.path.join(test_workspace, pipeline)
    results_path = os.path.join(pipeline_root,
                                "runners",
                                "dlstreamer",
                                "results",
                                "default",
                                measurement,
                                "result.json")
    assert(os.path.isfile(results_path))
    with open(results_path) as results_file:
        result = json.load(results_file)
        assert(measurement in result)
        
def check_download(pipeline):
    pipeline_root = os.path.join(test_workspace, pipeline)
    subfolders = ["media", "models", "runners"]

    for subfolder in subfolders:
        assert(os.path.isdir(os.path.join(pipeline_root,subfolder)))        
        

@pytest.mark.timeout(120)
def test_download(pipeline):
    test_cmd = "pipebench --workspace {} download {} --force ".format(test_workspace,pipeline)
    
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

@pytest.mark.timeout(300)
def test_throughput(pipeline):
    test_cmd = "pipebench --workspace {} measure {}".format(test_workspace,pipeline)
    
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


@pytest.mark.timeout(300)
def test_density(pipeline):
    test_cmd = "pipebench --workspace {} measure {} --density".format(test_workspace,pipeline)
    
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


