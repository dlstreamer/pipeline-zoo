#include <stdio.h>
#include <string.h>
#include "sm.h"
#include "utils.h"

void sys_mon_init(struct SysMonStat *sm)
{
	memset(sm, 0, sizeof(struct SysMonStat));
	gst_ru_cpu_init(&sm->cpu);
	init_power_consumption_metrics(&sm->cpu.pwr_stat_ref);
	gst_ru_gpu_init(&sm->gpu);
}

void sys_mon_finalize(struct SysMonStat *sm)
{
	finalize_power_consumption_metrics(&sm->cpu.pwr_stat_ref);
	gst_ru_cpu_finalize(&sm->cpu);
	//gst_ru_gpu_finalize(&sm->gpu);
	memset(sm, 0, sizeof(struct SysMonStat));
}

enum ProcStatReaderErrors sys_mon_compute(struct SysMonStat *sm)
{
	enum ProcStatReaderErrors error_code;

	sm->timestamp_s = get_current_time(MSEC);
	gst_ru_cpu_compute(&sm->cpu);
	fill_cpu_power_consumption(&sm->cpu.pwr_stat_ref);
	gst_ru_gpu_compute(&sm->gpu);
	if (sm->pid != -1) 
    {
	    error_code = gst_ru_proc_stat_read(&sm->proc, sm->pid);
    }
	sm->timestamp_e = get_current_time(MSEC);

	return error_code;
}

void sys_mon_setpid(struct SysMonStat *sm, int pid)
{
	if(sm) {
		sm->pid = pid;
		memset(&sm->proc, 0, sizeof(struct GstProcStatInterim));
	}
}
