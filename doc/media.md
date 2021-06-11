# Media Files

Media files for the pipeline zoo are stored in a git lfs repository
[media](https://gitlab.devtools.intel.com/media-analytics-pipeline-zoo/media)
and downloaded by pipebench on demand. 

## Adding Media

New media can be added to the repository following these steps.

1. Mount the new media files into a pipeline zoo container

   ```
   ./pipeline-zoo/tools/docker/run.sh -v /home/nnshah1/new_media:/home/new_media

   ```
1. Use the pipeline zoo upload utility to create a basic preview and readme for the media.
   
   ```
   python3 /home/pipeline-zoo/tools/uploader/upload -t media face-demographics-walking-2min.mp4
   chmod a+rx -R /home/new_media/video
   ```

1. Exit the container and clone the media repository

   ```
   git lfs install
   git clone ssh://git@gitlab.devtools.intel.com:29418/media-analytics-pipeline-zoo/media.git
   ```

1. Copy the new files into the repository

   ```
   cp -rf /home/nnshah1/new_media/video/* media/video
   ```

1. Create a branch, add the files, and push 
   ```
   git checkout -b additional_media_files
   git add media/video
   git commit -m "adding files"
   git push origin additional_media_files
   ```
   
1. Make a merge request

