'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
import abc
import util
import os
import shutil
import mdutils
import ffmpeg
import yaml
import subprocess
import shlex
import tempfile
from util import create_directory
from util import print_action
import gitlab
import urllib.parse
import requests

class Handler(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, args):
        pass
    
    @abc.abstractmethod
    def download(self,
                 pipeline,
                 pipeline_root,
                 item=None,
                 item_list=None):
        pass


def load_document(document_path):
    document = None
    with open(document_path) as document_file:
        if (document_path.endswith('.yml')):
            document = yaml.full_load(document_file)
        elif (document_path.endswith('.json')):
            document = json.load(document_file)
    return document

class Runner(Handler):
    def __init__(self,args):
        self._args = args

    def _build_runner(self,
                      document,
                      runner_root):

        default_build = os.path.join(runner_root,"build.sh")
        
        if (document and "build" in document):

            if (not isinstance (document["build"],list)):
                build_commands = [document["build"]]
            else:
                build_commands = document["build"]
                
            for build_command in build_commands:    
                build_command = shlex.split(build_command)

                result = subprocess.run(build_command,cwd=runner_root)

                if (result.returncode!=0):
                    return False
        elif (os.path.isfile(default_build)):
            build_command = ["/bin/bash",default_build]
            result = subprocess.run(build_command,cwd=runner_root)
            if (result.returncode!=0):
                return False

        return True
        
    def download(self,
                 pipeline,
                 pipeline_root,
                 item = None,
                 item_list = None):

        runners = [filepath for filepath in os.listdir(pipeline_root)
                   if os.path.isfile(os.path.join(pipeline_root,filepath))
                   and (filepath.endswith(".config.yml") or filepath.endswith(".config.json")) ]

        for runner_config in runners:

            runner_name = os.path.splitext(os.path.splitext(runner_config)[0])[0]

            if (item) and (runner_name!=item):
                continue
            
            source = os.path.join(self._args.runners_root, runner_name)
            target_root = os.path.join(self._args.destination,
                                       os.path.join(pipeline,"runners"))
            target_runner = os.path.join(target_root,runner_name)
            
            if (self._args.force):
                try:
                    shutil.rmtree(target_runner)
                except:
                    pass

            if os.path.isdir(target_runner):
                print("Runner Directory {0} Exists - Skipping".format(runner_name))
                continue
            
            shutil.copytree(source,target_runner)

            config_filepath = os.path.join(pipeline_root,
                                           runner_config)

            document = load_document(config_filepath)

            self._build_runner(document,
                               target_runner)
        


class Media(Handler):
    
    LFS_POINTER_SIZE = 200

    def __init__(self,args):
        self._args = args

    def _lfs(self, path):
        try:
            if os.path.getsize(path) <= Media.LFS_POINTER_SIZE:
                with open(path) as f:
                    for line in f:
                        if ("git-lfs" in line):
                            return True
        except Exception as error:
            print(error)
        return False
        
    def _download_lfs(self, path, target_path):
        url = "{}/-/raw/main/{}".format(self._args.media_root,path)
        print(url,flush=True)
        request = requests.get(url,allow_redirects=True)
        
        with open(target_path,"wb") as f:
            f.write(request.content)
    
    def _copy_gitlab_tree(self,path,target):
        parsed_url = urllib.parse.urlparse(self._args.media_root)
        gl = gitlab.Gitlab("{}://{}".format(parsed_url.scheme,parsed_url.netloc))
        project = gl.projects.get(parsed_url.path[1:])
        file_paths = project.repository_tree(path)
        for file_path in file_paths:
            target_path = os.path.join(target, file_path["path"])            
            os.makedirs(os.path.dirname(target_path),exist_ok=True)
            with open(target_path, 'wb') as f:
                project.files.raw(file_path=file_path["path"], ref='main', streamed=True, action=f.write)

            if (self._lfs(target_path)):
                self._download_lfs(file_path["path"], target_path)
            
    def download(self,
                 pipeline,
                 pipeline_root,
                 item=None,
                 item_list= None):


        media_list_path = os.path.join(pipeline_root,
                                       "media.list.yml")

        media_list = load_document(media_list_path)
        
        for media in media_list:

            if (item) and (item != media):
                continue

            
            target_root = os.path.join(self._args.destination,
                                       os.path.join(pipeline,"media"))
            target_media = os.path.join(target_root,media)

            if (self._args.force):
                try:
                    shutil.rmtree(target_media)
                except:
                    pass
            
            if os.path.isdir(target_media):
                print("Media Directory {0} Exists - Skipping".format(media))
                continue
            
            self._copy_gitlab_tree(media, target_root)
            
class Pipeline(Handler):
    def __init__(self,args):
        self._args = args
    def download(self,
                 pipeline,
                 pipeline_root,
                 item = None,
                 item_list = None):

        target_pipeline = os.path.join(self._args.destination,
                                       pipeline)
        
        if (self._args.force):
            try:
                shutil.rmtree(target_pipeline)
            except:
                pass

        if os.path.isdir(target_pipeline):
            print("Pipeline Directory {0} Exists - Skipping".format(pipeline))
            return 

        shutil.copytree(pipeline_root,target_pipeline)
        

class Model(Handler):

#    dldt_root = "/opt/intel/dldt/"
    dldt_root = "/opt/intel/openvino/deployment_tools"
    model_downloader = os.path.join(dldt_root,"open_model_zoo/tools/downloader/downloader.py")

    model_converter = os.path.join(dldt_root,"open_model_zoo/tools/downloader/converter.py")

    model_optimizer = os.path.join(dldt_root,"model_optimizer/mo.py")

    model_proc_root = "/opt/intel/dl_streamer/samples/model_proc"
    
    def __init__(self, args):
        self._args = args


    def _create_download_command(self, model, output_dir):
        return shlex.split("python3 {0} --name {1} -o {2}".format(Model.model_downloader,
                                                                  model,
                                                                  output_dir))

    def _create_convert_command(self, model, output_dir):
        return shlex.split("python3 {0} -d {2} --name {1} -o {2} --mo {3}".format(Model.model_converter,
                                                                           model,output_dir,Model.model_optimizer))


    def _find_model_root(self,model,output_dir):
        
        for root, directories, files in os.walk(output_dir):
            if (model in directories):
                return os.path.abspath(os.path.join(root,model))
        return None

    def _find_model_proc(self, model):
        for root, directories, files in os.walk(Model.model_proc_root):
            for filepath in files:
                if os.path.splitext(filepath)[0]==model:
                    return os.path.join(root,filepath)
        
    
    def _download_and_convert_model(self, pipeline, pipeline_root, model):

        target_root = os.path.join(self._args.destination,
                              os.path.join(pipeline,"models"))
        target_model = os.path.join(target_root,model)

        if (not self._args.force) and (os.path.isdir(target_model)):
            print("Model Directory {0} Exists - Skipping".format(model))
            return
        
        with tempfile.TemporaryDirectory() as output_dir:
            command = self._create_download_command(model,output_dir)
            print(' '.join(command))
            subprocess.run(command)
            command = self._create_convert_command(model,output_dir)
            print(' '.join(command))
            subprocess.run(command)
            model_path = self._find_model_root(model,output_dir)
            
            create_directory(target_root,False)
            
            shutil.move(model_path,target_root)
            model_proc = self._find_model_proc(model)
            if (model_proc):
                shutil.copy(model_proc,target_model)
            
        
    def download(self, pipeline, pipeline_root, item = None, item_list = None):
        
        model_list_path = os.path.join(pipeline_root,"models.list.yml")

        model_list = load_document(model_list_path)
        
        for model in model_list:
            self._download_and_convert_model(pipeline,pipeline_root,model)
