#ifndef __GST_CPU_USAGE_COMPUTE_H__
#define __GST_CPU_USAGE_COMPUTE_H__

#include "pwrstat.h"

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

struct GstCPUStatInterim {
	/* CPU core number */
	int cpu_num;
	float *cpu_load;

	int *user; /* Time spent in user mode */
	int *user_aux; /* Time spent in user mode */
	int *nice; /* Time spent in user mode with low priority */
	int *nice_aux; /* Time spent in user mode with low priority */
	int *system; /* Time spent in user mode with low priority */
	int *system_aux; /* Time spent in user mode with low priority */
	int *idle; /* Time spent in system mode */
	int *idle_aux; /* Time spent in system mode */
	bool cpu_array_sel;

	float *cpu_frequency;
	bool cpu_frequency_available;

	unsigned long mem_total;
	unsigned long mem_free;
	unsigned long mem_used;

	struct PowerStatInterim pwr_stat_ref; /*Power consumption statistics*/
} GstCPUStatInterim;

void gst_ru_cpu_init(struct GstCPUStatInterim *cpu_stat_ref);
void gst_ru_cpu_finalize(struct GstCPUStatInterim *cpu_stat_ref);

void gst_ru_cpu_compute(struct GstCPUStatInterim *cpu_stat_ref);

#ifdef __cplusplus
}
#endif

#endif //__GST_CPU_USAGE_COMPUTE_H__
