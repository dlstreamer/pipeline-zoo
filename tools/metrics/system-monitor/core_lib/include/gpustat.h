#ifndef __GST_GPU_USAGE_COMPUTE_H__
#define __GST_GPU_USAGE_COMPUTE_H__

//#include <jmorecfg.h>
#include <stdbool.h>

struct GstGPUStatHwBlock {
	const char *dispName;
	float sema;
	float wait;
	float busy;
};

struct GstGPUStatInterim {
	float freq_req;
	float freq_act;
	float irq;
	float rc6;
	float imc_reads;
	float imc_writes;
	void *engines;
	bool isFirstTime;
	struct GstGPUStatHwBlock blocks[5]; //TODO make dynamic
};

void gst_ru_gpu_init(struct GstGPUStatInterim *gpu_stat_ref);

void gst_ru_gpu_compute(struct GstGPUStatInterim *gpu_stat_ref);

#endif //__GST_GPU_USAGE_COMPUTE_H__
