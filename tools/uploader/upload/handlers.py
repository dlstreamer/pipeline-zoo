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
import hashlib

class Handler(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, args):
        pass
    
    @abc.abstractmethod
    def prepare(self):
        pass

    def _calculate_file_size(self, file_path):
        return os.path.getsize(file_path)

    def _calulate_sha256(self, file_path):
        sha256 = hashlib.sha256()
        block_size=65536
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha256.update(block)
        return sha256.hexdigest()

class Media(Handler):

    media_types = {'video':['QuickTime / MOV','raw HEVC video','raw H.264 video']}
    
    def __init__(self, args):
        self._args = args

    def _determine_media_type(self,media_info):
        for media_type, long_formats in Media.media_types.items():
            if (media_info['format']['format_long_name'] in long_formats):
                return media_type
            else:
                print("unknown media type: {0}".format(media_info['format']['format_long_name']))

    def _create_preview(self,media_filename, directory):
   
        palette = os.path.join(directory, "palette.png")
        (
            ffmpeg
            .input(media_filename,t=5)
            .filter('fps',12)
            .filter('scale',500,-1)
            .filter('palettegen')
            .output(palette)
            .run()
        )

        stream = (
            ffmpeg
            .input(media_filename,t=5)
            .filter('fps',12)
            .filter('scale',500,-1)
        )

        palette_input = (
            ffmpeg
            .input(palette)
        )

        output_gif = os.path.join(directory, "preview.gif")
        (
            ffmpeg
            .filter((stream,palette_input),"paletteuse")
            .output(output_gif)
            .run()
        )
        os.remove(palette)
        return output_gif
    
    def prepare(self):

        media_info = ffmpeg.probe(self._args.source)

        media_type = self._determine_media_type(media_info) 
        
        basename = os.path.basename(self._args.source)
        subdirectory = os.path.join(media_type,os.path.splitext(basename)[0])
        directory = os.path.join(self._args.destination,subdirectory)
        util.create_directory(directory)
        media_filename = os.path.join(directory,basename)
        shutil.copyfile(self._args.source,media_filename)

        preview = self._create_preview(media_filename,directory)
        
        readme = mdutils.MdUtils(file_name=os.path.join(directory,"README.md"),title=os.path.basename(subdirectory))
        readme.new_line(readme.new_inline_image("Preview",os.path.basename(preview)))
        readme.create_md_file()

        self._prepare_description(os.path.basename(subdirectory), os.path.basename(self._args.source), os.path.join(directory,"media.yml"))



    def _prepare_description(self, description, media_name, description_path):
        self._args.source
        description = {"description" : description, "files" : {"name" : media_name, "sha256" : self._calulate_sha256(self._args.source), "size" : self._calculate_file_size(self._args.source), "source" : "PUT URL HERE"}, "license" : "https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/LICENSE"}

        with open(description_path, 'w') as file:
                yaml.dump(description, file)

class Model(Handler):
    def __init__(self, args):
        self._args = args
    def prepare(self):
        directory = os.path.join(self._args.destination, os.path.basename(self._args.source))
        model_files = []
        for model_file in os.listdir(self._args.source):
            model_files.append(os.path.join(self._args.source, model_file))

        self._prepare_description(os.path.basename(self._args.source), model_files, os.path.join(directory,"model.yml"))

        
    def _prepare_description(self, model_name, model_files, description_path):
        files_descriptions = []
        
        for file in model_files:
            file_desctiption = {"name" : os.path.basename(file), "sha256" : self._calulate_sha256(file), "checksum" : self.calculate_sha384(file), "size" : self._calculate_file_size(file), "source" : "PUT URL HERE"}
            files_descriptions.append(file_desctiption)
        description = {"description" : model_name, "files" : files_descriptions, "framework": "dldt", "task_type": "model task type" "license" : ""}

        with open(description_path, 'w') as file:
                yaml.dump(description, file)

    def calculate_sha384(self, file_path):
        sha384 = hashlib.sha384()
        block_size=65536
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha384.update(block)
        
        return sha384.hexdigest()