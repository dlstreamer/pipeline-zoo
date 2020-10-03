using the docker file 

From the root folder 
```system-monitor``` run the build docker image script

```
./docker/build.sh
```

A docker image by the name `collector:build` will be created 

Run this docker image using 

```
./docker/run.sh
```

This will create a file .csv file in the same location