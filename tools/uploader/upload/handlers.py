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

class Handler(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, args):
        pass
    
    @abc.abstractmethod
    def prepare(self):
        pass

class Media(Handler):

    media_types = {'video':['QuickTime / MOV']}
    
    def __init__(self, args):
        self._args = args

    def _determine_media_type(self,media_info):
        for media_type, long_formats in Media.media_types.items():
            if (media_info['format']['format_long_name'] in long_formats):
                return media_type

    def _create_sample_frame(self,media_filename, directory):
        output_filename = os.path.join(directory,"sample_frame.png")
        (
            ffmpeg
            .input(media_filename,ss=5)
            .filter('scale',500,-1)
            .output(output_filename,vframes=1)
            .run()
        )
        return output_filename
    
    def prepare(self):

        media_info = ffmpeg.probe(self._args.source)

        media_type = self._determine_media_type(media_info) 
        
        basename = os.path.basename(self._args.source)
        subdirectory = os.path.join(media_type,os.path.splitext(basename)[0])
        directory = os.path.join(self._args.destination,subdirectory)
        util.create_directory(directory)
        media_filename = os.path.join(directory,basename)
        shutil.copyfile(self._args.source,media_filename)

        sample_frame_filename = self._create_sample_frame(media_filename,directory)
        
        readme = mdutils.MdUtils(file_name=os.path.join(directory,"README.md"),title=os.path.basename(subdirectory))
        readme.new_line(readme.new_inline_image("Sample",os.path.basename(sample_frame_filename)))
        readme.create_md_file()
        
        
