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

timeout_sec = 60
#TODO: don't hardcode dst here 
dst = "/home/tools/pipebench/workspace"     

def pytest_report_header(config):
    return "test downalod command of pipebench"


def run_cmd(cmd_str):
    exec_cmd = "timeout " + str(timeout_sec) + " " + cmd_str 
    proc = subprocess.Popen(shlex.split(exec_cmd), stderr=subprocess.PIPE, shell=False) 
    stderr = proc.communicate()
    exitcode = proc.returncode
    return exitcode, stderr


def parse_yml_file(filename):
    with open(filename, 'r') as out:
        try:
            yaml_dict = yaml.safe_load(out)
            return yaml_dict
        except yaml.YAMLError as ex:
            pytest.fail("yaml content could not be parsed " + ex)  

def check_content(yml_dict):
    global dst
    try:
        ppl_path = os.path.join(dst, yml_dict['pipeline'])
        models_path =  os.path.join(dst, yml_dict['pipeline'], 'models')
        media_path =  os.path.join(dst, yml_dict['pipeline'], 'media', yml_dict['media'])
        runners_path =  os.path.join(dst, yml_dict['pipeline'], 'runners')
        filelist = glob.glob(ppl_path + '/**/*', recursive=True) 

        assert(os.path.isdir(ppl_path))
        assert(os.path.isdir(models_path))
        assert(os.path.isdir(media_path))
        assert(os.path.isdir(runners_path))
        
        assert(filelist.count(models_path + "/mobilenet-ssd/FP16/mobilenet-ssd.bin") == 1)
        assert(filelist.count(models_path + "/mobilenet-ssd/FP16/mobilenet-ssd.xml") == 1)
        assert(filelist.count(models_path + "/mobilenet-ssd/FP16/mobilenet-ssd.mapping") == 1)
        assert(filelist.count(models_path + "/mobilenet-ssd/FP32/mobilenet-ssd.bin") == 1)
        assert(filelist.count(models_path + "/mobilenet-ssd/FP32/mobilenet-ssd.xml") == 1)
        assert(filelist.count(models_path + "/mobilenet-ssd/FP32/mobilenet-ssd.mapping") == 1)

        #total_file_count = len(filelist) 
        #assert(total_file_count == 27)
        
    except:
        pytest.fail("pipeline folder content is invalid");

#pytest 
def test_command_download(yml_filename="test.workload.yml"):
    test_cmd = "python3 pipebench --workload " + yml_filename + " download --force"
    yml_dict = parse_yml_file(yml_filename);
    
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
    check_content(yml_dict)

#test_command_download()
