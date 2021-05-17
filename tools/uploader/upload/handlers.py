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
        
        
