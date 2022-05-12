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
import json
import subprocess
import shlex
import tempfile
from util import create_directory
import gitlab
from github import Github
import github
import urllib.parse
import requests
import hashlib
import netrc
from tqdm import tqdm
import sys
from util import Spinner
import logging

class Handler(object, metaclass=abc.ABCMeta):
    logger = None
    @abc.abstractmethod
    def __init__(self, args):
        pass

    def _init_logger(self, pipeline_root, args):
        if Handler.logger != None:
            return

        Handler.logger = logging.getLogger("downloader")
        Handler.logger.setLevel(logging.DEBUG)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.INFO)

        log_dir = os.path.join(pipeline_root, ".logs")
        os.makedirs(log_dir, exist_ok=True)
        fileHandler = logging.FileHandler(os.path.join(log_dir, "download.log.txt"), mode='w')
        fileHandler.setLevel(logging.DEBUG)

        if args.verbose > 1:
            consoleHandler.setLevel(logging.DEBUG)
            Handler.logger.setLevel(logging.DEBUG)

        Handler.logger.addHandler(consoleHandler)
        Handler.logger.addHandler(fileHandler)

    @staticmethod
    def print_action(action,details=[]):
        Handler.logger.info("")
        banner = "="*len(action) 
        Handler.logger.info(banner)
        Handler.logger.info(action)
        Handler.logger.info(banner)
        for detail in details:
            Handler.logger.info("\t{}".format(detail))
        Handler.logger.info("")



    
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

        if self._args.verbose < 2:
            spinner = Spinner(text='Building')
            spinner.start()

        default_build = os.path.join(runner_root,"build.sh")
        
        return_code = 1

        if (document and "build" in document):

            if (not isinstance (document["build"],list)):
                build_commands = [document["build"]]
            else:
                build_commands = document["build"]

            return_code = 0

            for build_command in build_commands:    
                build_command = shlex.split(build_command)

                result = subprocess.run(build_command,cwd=runner_root)

                return_code = result.returncode 

                if return_code != 0:
                    return False

        elif (os.path.isfile(default_build)):
            build_command = ["/bin/bash",default_build]

            process = subprocess.Popen(build_command,cwd=runner_root, bufsize=1, universal_newlines=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

            for line in process.stdout:              
                self.logger.debug(line)
                sys.stdout.flush()

            process.stdout.close()

            return_code = process.wait()

        if self._args.verbose < 2:
                spinner.stop()

        return return_code == 0
        
    def download(self,
                 pipeline,
                 pipeline_root,
                 item = None,
                 item_list = None):

        runners = [filepath.split('.')[0]+".runner-settings.yml" for filepath in os.listdir(pipeline_root)
                   if os.path.isfile(os.path.join(pipeline_root,filepath))
                   and (filepath.endswith(".runner-settings.yml"))]

        if runners:
            Handler.print_action("Downloading Runners")

        runners = set(runners)

        for runner_config in runners:

            runner_name = runner_config.replace(".runner-settings.yml","")

            if (item) and (runner_name!=item):
                continue

            self.logger.info(msg = "Download {0}".format(runner_name))
            
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
                self.logger.debug("Runner Directory {0} Exists - Skipping".format(runner_name))
                continue
            
            shutil.copytree(source,target_runner)

            config_filepath = os.path.join(pipeline_root,
                                           runner_config)

            document = load_document(config_filepath)

            self._build_runner(document,
                               target_runner)

        return True

class GithubUrlConverter:
    def __init__(self):
        self._github = self._connect_to_repo()

    def convert(self, original_url):
        converted_url = original_url

        url_info = urllib.parse.urlparse(original_url)

        if  "github.com" in url_info.netloc:
            repo_name = url_info.path.split("/")[1] + "/" + url_info.path.split("/")[2]
            try:
                repo = self._github.get_repo(repo_name)
            except:
                return original_url

            converted_url = self._get_download_url(repo, url_info.path.split("/")[-1], "/".join(url_info.path.split("/")[5:-1]))

        return converted_url

    def _get_lfs_download_url(self, repo, file_path):
        file_content = repo.get_contents(file_path)
        return file_content.download_url

    def _get_download_url(self, repo, file_name, file_dir):
        files_content = repo.get_dir_contents(file_dir)
        for file_content in files_content:
                if file_content.name == file_name:
                    if file_content.size > 200:
                        return file_content.download_url
                    else:
                        return self._get_lfs_download_url(repo, os.path.join(file_dir, file_name))

        return None

    def _connect_to_repo(self):

        token = os.getenv('GITHUB_TOKEN')

        if not token:
            try:
                netrc_file = netrc.netrc()
                auth_tokens = netrc_file.authenticators("github.com")
                token = auth_tokens[2]
            except:
                token=None

        github = Github(token)
        return github


class Media(Handler):
    def __init__(self, args):
        self._args = args
        self._media_descriptions_root = os.path.abspath(
            os.path.join(__file__,
                         "../../../../media/descriptions"))

    def _get_media_list(self, pipeline_root):
        media_list = []
        for path in os.listdir(pipeline_root):
            if path.endswith("media.list.yml"):
                media_list.extend(load_document(os.path.join(pipeline_root,path)))
        return media_list
        

    def download(self,
                 pipeline,
                 pipeline_root,
                 item=None,
                 item_list= None):

        media_list = self._get_media_list(pipeline_root)
        
        if media_list:
            Handler.print_action("Downloading Media")
        
        for media in media_list:
            if (item) and (item != media):
                continue
            
            target_root_path = os.path.join(self._args.destination,
                                       os.path.join(pipeline,"media"))
            target_media_path = os.path.join(target_root_path, media)

            if (self._args.force):
                try:
                    shutil.rmtree(target_media_path)
                except:
                    pass
            
            if os.path.isdir(target_media_path):
                self.logger.debug("Media Directory {0} Exists - Skipping".format(media))
                continue
            
            if not self._process_config(media, target_root_path):
                return False

        return True

    def _get_media_config_file(self, media_config_path):
        yaml_path = os.path.join(self._media_descriptions_root, media_config_path)
        yaml_path = os.path.join(yaml_path, "media.yml")
        contents = load_document(yaml_path)
        return contents

    def _process_config(self, media_config_path, target_path):
        config_file = self._get_media_config_file(media_config_path)
        target = os.path.join(target_path, media_config_path)
        os.makedirs(target, exist_ok=True)

        for file in config_file["files"]:
            media_file = os.path.join(target, file["name"])
            if not self._download_media(file["source"], media_file, file["name"]):
                return False

            if not self._check_size(media_file, file["size"]) or not self._check_hash(media_file, file["sha256"]):
                os.remove(media_file)
                return False

            if "convert-command" in file:
                self._ffmpeg_convert(media_file, file["convert-command"])

        return True

    def _download_media(self, url, target_path, file_name):
        self.logger.info(msg = "Downloading: {}".format(file_name))

        if self._args.verbose:
            self.logger.info("\tURL: {}\n\tPATH: {}".format(url, target_path))

        url_converter = GithubUrlConverter()
        url = url_converter.convert(url)

        response = requests.get(url,allow_redirects=True, stream=True)
        total_size_in_bytes= int(response.headers.get('content-length', 0))

        if response.status_code != 200:
            self.logger.error("\tError: Return code: {}".format(response.status_code))
            return False

        block_size = 1024 #1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(target_path, "wb") as f:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                f.write(data)
        progress_bar.close()

        return True

    def _check_size(self, file_path, expected_size):
        download_size = os.path.getsize(file_path)
        if download_size != expected_size:
            self.logger.error("\tError downloaded size {0} is not equal expected size {1}".format(download_size, expected_size))
            return False

        return True

    def _check_hash(self, file_path, expected_hash):
        sha256 = hashlib.sha256()
        block_size=65536
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha256.update(block)
        
        if sha256.hexdigest() != expected_hash:
            self.logger.error("\tError downloaded hash {0} is not equal expected hash {1}".format(sha256.hexdigest(), expected_hash))
            return False

        return True

    def _ffmpeg_convert(self, source_path, command):
        self.logger.info(msg = "\tFFMPEG Converting")
        ffmpeg_cmd = ["ffmpeg", '-i', source_path]
        ffmpeg_args = shlex.split(command)
        
        output_file_name = ffmpeg_args[-1]

        output_file = os.path.join(os.path.dirname(source_path), output_file_name)
        ffmpeg_args[-1] = output_file
        ffmpeg_cmd = ffmpeg_cmd + ffmpeg_args

        if self._args.verbose < 2:
                spinner = Spinner(text='Converting')
                spinner.start()

        process = subprocess.Popen(ffmpeg_cmd, universal_newlines=True, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.PIPE, shell=False, stdin=subprocess.DEVNULL)

        for line in iter(process.stderr):
            self.logger.debug(line)

        return_code = process.wait()

        if self._args.verbose < 2:
            spinner.stop()

        return return_code == 0
            
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
            self._init_logger(pipeline, self._args)
            self.logger.debug("Pipeline Directory {0} Exists - Skipping".format(pipeline))
            return 

        shutil.copytree(pipeline_root,target_pipeline)

        self._init_logger(pipeline, self._args)

        return True
        

class Model(Handler):

    openvino_root = os.environ.get("INTEL_OPENVINO_DIR", "/opt/intel/openvino")
    
    dldt_root =  os.path.join(openvino_root, "deployment_tools")

    model_proc_root = os.environ.get("DLSTREAMER_MODEL_PROC_ROOT",
                                     "/opt/intel/openvino/data_processing/dl_streamer/samples/model_proc")

    pipeline_zoo_models_root = os.path.join(dldt_root,"open_model_zoo/models", "pipeline-zoo-models")
    
    def __init__(self, args):
        self._args = args
        self._model_descriptions_root = os.path.abspath(
            os.path.join(__file__,
                         "../../../../models/descriptions"))

        self._model_downloader = os.path.join(self.dldt_root,"open_model_zoo/tools/downloader/downloader.py")
        self._model_converter = os.path.join(self.dldt_root,"open_model_zoo/tools/downloader/converter.py")
        self._model_optimizer = os.path.join(self.dldt_root,"model_optimizer/mo.py")

        self._openvino_version = []

        self._get_openvino_version()
        self._get_open_model_zoo_tools()

    def _get_openvino_version(self):
        openvino_dir = self.openvino_root

        if os.path.islink(self.openvino_root):
            openvino_dir = os.path.realpath(self.openvino_root)

        openvino_name = os.path.basename(openvino_dir)
        version_parts = str(openvino_name).replace("openvino_", "").split(".")

        for version_part in version_parts:
            try:
                self._openvino_version.append(int(version_part))
            except:
                self.logger.error("OpenVINO(TM) toolkit version is not number: " + str(version_part))
                self._openvino_version.append(0)


        return self._openvino_version

    def _get_open_model_zoo_tools(self):
        if self._openvino_version[0] > 2021:
            self._model_downloader = os.path.join(self.dldt_root,"open_model_zoo/tools/model_tools/downloader.py")
            self._model_converter = os.path.join(self.dldt_root,"open_model_zoo/tools/model_tools/converter.py")

        
    def _create_download_command(self, model, output_dir):
        return shlex.split("python3 {0} --name {1} -o {2}".format(self._model_downloader,
                                                                  model,
                                                                  output_dir))

    def _create_convert_command(self, model, output_dir):
        return shlex.split("python3 {0} -d {2} --name {1} -o {2} --mo {3}".format(self._model_converter,
                                                                           model,output_dir, self._model_optimizer))


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

    def _update_model_config(self, model_path, model):
        model_path = os.path.join(model_path, "model.yml")
        target_path = os.path.join(Model.pipeline_zoo_models_root, model, "model.yml")
        model_config = load_document(model_path)

        for file in model_config["files"]:
            url_covnerter = GithubUrlConverter()
            url = url_covnerter.convert(file["source"])
            file["source"] = url
            if self._openvino_version[0] > 2021:
                del file["sha256"]
        create_directory(os.path.join(Model.pipeline_zoo_models_root,model))
        with open(target_path, 'w') as model_description_file:
            yaml.dump(model_config, model_description_file)

    def _download_and_convert_model(self, pipeline, pipeline_root, model):
        for model_dir in os.listdir(self._model_descriptions_root):
            if model_dir == model:
                self._update_model_config(os.path.join(self._model_descriptions_root, model_dir),
                                         model)

        target_root = os.path.join(self._args.destination,
                              os.path.join(pipeline,"models"))
        target_model = os.path.join(target_root,model)

        if (not self._args.force) and (os.path.isdir(target_model)):
            self.logger.debug("Model Directory {0} Exists - Skipping".format(model))
            return
        
        with tempfile.TemporaryDirectory() as output_dir:
            command = self._create_download_command(model,output_dir)
            
            self.logger.debug("Download command: {0}".format(" ".join(command)))

            process = subprocess.Popen(command, bufsize=1, universal_newlines=True, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
            for line in process.stdout:
                self.logger.debug(line)
                sys.stdout.flush()

            process.stdout.close()
            process.wait()

            if model!="mobilenetv2_7":
                command = self._create_convert_command(model,output_dir)
                self.logger.debug("Convert command: {0}".format(" ".join(command)))

            process = subprocess.Popen(command, bufsize=1, universal_newlines=True, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)

            for line in process.stdout:
                self.logger.debug(line)

                sys.stdout.flush()

            process.stdout.close()

            process.wait()

            model_path = self._find_model_root(model,output_dir)
            
            self.logger.debug("Creating direcory: {}".format(target_root))
            create_directory(target_root,False)
            
            shutil.move(model_path,target_root)
            model_proc = self._find_model_proc(model)
            if (model_proc):
                shutil.copy(model_proc,target_model)

    def _get_model_list(self, pipeline_root):
        model_list = []
        for path in os.listdir(pipeline_root):
            if path.endswith("models.list.yml"):
                model_list.extend(load_document(os.path.join(pipeline_root,path)))
        return model_list
    
    def download(self, pipeline, pipeline_root, item = None, item_list = None):
        
        model_list = self._get_model_list(pipeline_root)

        if model_list:
            Handler.print_action("Downloading Models")
        
        for model in model_list:
            self.logger.info(msg = "Download: {0}".format(model))

            if self._args.verbose < 2:
                spinner = Spinner(text='Loading')
                spinner.start()

            self._download_and_convert_model(pipeline,pipeline_root,model)

            if self._args.verbose < 2:
                spinner.stop()

        return True
