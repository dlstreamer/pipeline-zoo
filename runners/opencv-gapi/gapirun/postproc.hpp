#pragma once

namespace postproc {


  struct ObjectDetectionResult{
    cv::Rect roi;
    float image_id;
    float confidence;
    float roi_left;
    float roi_top;
    float roi_right;
    float roi_bottom;
    float object_type;
    cv::Size resolution;
    ObjectDetectionResult(float image_id,
			  float object_type,
			  float confidence,
			  float roi_left,
			  float roi_top,
			  float roi_right,
			  float roi_bottom,
			  const cv::Size &resolution
			 ):image_id(image_id),
			   object_type(object_type),
			   confidence(confidence),
			   roi_top(roi_top),
			   roi_left(roi_left),
			   roi_bottom(roi_bottom),
			   roi_right(roi_right),
			   resolution(resolution)
    {}

  };


//! [Postproc]
// SSD Post-processing function - this is not a network but a kernel.
// The kernel body is declared separately, this is just an interface.
// This operation takes two Mats (detections and the source image),
// and returns a vector of ROI (filtered by a default threshold).
// Threshold (or a class to select) may become a parameter, but since
// this kernel is custom, it doesn't make a lot of sense.
  using Detections = std::tuple<cv::GArray<ObjectDetectionResult>, cv::GArray<cv::Rect>>;
  G_API_OP(SSDPostProcCombined, <Detections(cv::GMat, cv::GMat)>, "postproc.ssd_postproc_combined") {
    static std::tuple<cv::GArrayDesc,cv::GArrayDesc> outMeta(const cv::GMatDesc &, const cv::GMatDesc &) {
      // This function is required for G-API engine to figure out
      // what the output format is, given the input parameters.
      // Since the output is an array (with a specific type),
      // there's nothing to describe.
      return std::make_tuple(cv::empty_array_desc(), cv::empty_array_desc());
    }
};


//! [Postproc]
// SSD Post-processing function - this is not a network but a kernel.
// The kernel body is declared separately, this is just an interface.
// This operation takes two Mats (detections and the source image),
// and returns a vector of ROI (filtered by a default threshold).
// Threshold (or a class to select) may become a parameter, but since
// this kernel is custom, it doesn't make a lot of sense.
//  using Detections = std::tuple<cv::GArray<ObjectDetectionResult>, cv::GArray<cv::Rect>>;
  G_API_OP(SSDPostProc, <cv::GArray<ObjectDetectionResult>(cv::GMat, cv::GMat)>, "postproc.ssd_postproc") {
    static cv::GArrayDesc outMeta(const cv::GMatDesc &, const cv::GMatDesc &) {
      // This function is required for G-API engine to figure out
      // what the output format is, given the input parameters.
      // Since the output is an array (with a specific type),
      // there's nothing to describe.
      return cv::empty_array_desc();
    }
};

//! [Postproc]
// SSD Post-processing function - this is not a network but a kernel.
// The kernel body is declared separately, this is just an interface.
// This operation takes two Mats (detections and the source image),
// and returns a vector of ROI (filtered by a default threshold).
// Threshold (or a class to select) may become a parameter, but since
// this kernel is custom, it doesn't make a lot of sense.
//  using Detections = std::tuple<cv::GArray<ObjectDetectionResult>, cv::GArray<cv::Rect>>;
  G_API_OP(ExtractRegions, <cv::GArray<cv::Rect>(cv::GArray<ObjectDetectionResult>)>, "postproc.extract_regions") {
    static cv::GArrayDesc outMeta(const cv::GArrayDesc &) {
      // This function is required for G-API engine to figure out
      // what the output format is, given the input parameters.
      // Since the output is an array (with a specific type),
      // there's nothing to describe.
      return cv::empty_array_desc();
    }
};


// OpenCV-based implementation of the above kernel.
GAPI_OCV_KERNEL(OCVExtractRegions, ExtractRegions) {
  static void run(const std::vector<ObjectDetectionResult> &in_objects,
		  std::vector<cv::Rect> &out_regions) {
    out_regions.clear();
    for (auto object : in_objects) {
      out_regions.push_back(object.roi);
    }
  }
};
  
// OpenCV-based implementation of the above kernel.
GAPI_OCV_KERNEL(OCVSSDPostProc, SSDPostProc) {
    static void run(const cv::Mat &in_ssd_result,
                    const cv::Mat &in_frame,
                    std::vector<ObjectDetectionResult> &out_objects) {
        const int MAX_PROPOSALS = 200;
        const int OBJECT_SIZE   =   7;
        const cv::Size upscale = in_frame.size();
        const cv::Rect surface({0,0}, upscale);
	
        out_objects.clear();
	//	out_regions.clear();

        const float *data = in_ssd_result.ptr<float>();
        for (int i = 0; i < MAX_PROPOSALS; i++) {

	  ObjectDetectionResult detection(data[i * OBJECT_SIZE + 0], // batch id
					  data[i * OBJECT_SIZE + 1],
					  data[i * OBJECT_SIZE + 2],
					  data[i * OBJECT_SIZE + 3],
					  data[i * OBJECT_SIZE + 4],
					  data[i * OBJECT_SIZE + 5],
					  data[i * OBJECT_SIZE + 6],
					  upscale);
					  
            if (detection.image_id < 0.f) {  // indicates end of detections
                break;
            }
            if (detection.confidence < 0.5f) { // a hard-coded snapshot
                continue;
            }

            // Convert floating-point coordinates to the absolute image
            // frame coordinates; clip by the source image boundaries.
            detection.roi.x      = static_cast<int>(detection.roi_left   * upscale.width);
            detection.roi.y      = static_cast<int>(detection.roi_top    * upscale.height);
            detection.roi.width  = static_cast<int>(detection.roi_right  * upscale.width)  - detection.roi.x;
            detection.roi.height = static_cast<int>(detection.roi_bottom * upscale.height) - detection.roi.y;
	    detection.roi = detection.roi & surface;
            out_objects.push_back(detection);
        }
    }
};


  
// OpenCV-based implementation of the above kernel.
GAPI_OCV_KERNEL(OCVSSDPostProcCombined, SSDPostProcCombined) {
    static void run(const cv::Mat &in_ssd_result,
                    const cv::Mat &in_frame,
                    std::vector<ObjectDetectionResult> &out_objects,
		    std::vector<cv::Rect> &out_regions) {
        const int MAX_PROPOSALS = 200;
        const int OBJECT_SIZE   =   7;
        const cv::Size upscale = in_frame.size();
        const cv::Rect surface({0,0}, upscale);
        out_objects.clear();
	out_regions.clear();

        const float *data = in_ssd_result.ptr<float>();
        for (int i = 0; i < MAX_PROPOSALS; i++) {

	  ObjectDetectionResult detection(data[i * OBJECT_SIZE + 0], // batch id
					  data[i * OBJECT_SIZE + 1],
					  data[i * OBJECT_SIZE + 2],
					  data[i * OBJECT_SIZE + 3],
					  data[i * OBJECT_SIZE + 4],
					  data[i * OBJECT_SIZE + 5],
					  data[i * OBJECT_SIZE + 6],
					  upscale);
					  
            if (detection.image_id < 0.f) {  // indicates end of detections
                break;
            }
            if (detection.confidence < 0.5f) { // a hard-coded snapshot
                continue;
            }

            // Convert floating-point coordinates to the absolute image
            // frame coordinates; clip by the source image boundaries.
            detection.roi.x      = static_cast<int>(detection.roi_left   * upscale.width);
            detection.roi.y      = static_cast<int>(detection.roi_top    * upscale.height);
            detection.roi.width  = static_cast<int>(detection.roi_right  * upscale.width)  - detection.roi.x;
            detection.roi.height = static_cast<int>(detection.roi_bottom * upscale.height) - detection.roi.y;
	    detection.roi = detection.roi & surface;
            out_objects.push_back(detection);
	    out_regions.push_back(detection.roi);
        }
    }
};


}
