DEVICES=(dGPU)
BATCH_SIZE=(1 64)
PRECISIONS=(FP16-INT8)
STREAMS_PER_PROCESS=(0)
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

#PIPELINES=(oc-h264-full_frame-efficientnet-b0)
#	   oc-h265-full_frame-efficientnet-b0)


for pipeline in "${PIPELINES[@]}"
do
   pipebench download $pipeline

   for device in "${DEVICES[@]}"
   do
       for batch in "${BATCH_SIZE[@]}"
       do
	   for streams in "${STREAMS_PER_PROCESS[@]}"
	   do
	       if [ "${streams}" == "1" ]; then
		   SYNC="--runner-override sink.sync true";
	       else
		   SYNC="--runner-override sink.sync false";
	       fi

	       SYNC="--runner-override sink.sync false";
	    
	       pipebench run $pipeline --measure density --runner-override detect.batch-size $batch --runner-override classify-0.batch-size $batch --platform dgpu --streams-per-process $streams $SYNC --search-method binary --target-fps 15 --measurement-directory "${device}_FP16_INT8_${batch}_${streams}" --max-processes 8 --duration 120 --force

	   done
       done
   done
done