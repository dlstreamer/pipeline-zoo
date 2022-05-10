DEVICES=(dGPU)
BATCH_SIZE=(1 64)
PRECISIONS=(FP16-INT8)
STREAMS_PER_PROCESS=(2 30)
PIPELINES=(oc-h264-full_frame-resnet-50-tf
 	   oc-h265-full_frame-resnet-50-tf
 	   oc-h264-full_frame-efficientnet-b0
 	   oc-h265-full_frame-efficientnet-b0
 	   oc-h264-ssdlite-mobilenet-v2-efficientnet-b0
 	   oc-h265-ssdlite-mobilenet-v2-efficientnet-b0
 	   od-h265-ssdlite-mobilenet-v2
 	   od-h264-ssdlite-mobilenet-v2
 	   od-h264-yolov5n
 	   od-h265-yolov5n
 	   od-h265-yolov5s
 	   od-h264-yolov5s)

#PIPELINES=(od-h265-yolov5s)

#PIPELINES=(oc-h264-full_frame-efficientnet-b0
#	   oc-h265-full_frame-efficientnet-b0)


for pipeline in "${PIPELINES[@]}"
do
   pipebench download $pipeline --force
done
