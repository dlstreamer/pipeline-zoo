#ifndef __SYS_MON_H__
#define __SYS_MON_H__

#include "cpustat.h"
#include "gpustat.h"
#include "procstatreader.h"

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

struct SysMonStat {
	struct GstCPUStatInterim cpu;
	struct GstGPUStatInterim gpu;
	struct GstProcStatInterim proc;
	/*Time in UTC with milliseconds when stat collection begun.*/
	unsigned long timestamp_s;
	/*Time in UTC with milliseconds when stat collection ended.*/
	unsigned long timestamp_e;
	int pid;
};

void sys_mon_init(struct SysMonStat *sm);
void sys_mon_finalize(struct SysMonStat *sm);

enum ProcStatReaderErrors sys_mon_compute(struct SysMonStat *sm);

void sys_mon_setpid(struct SysMonStat *sm, int pid);

#ifdef __cplusplus
}
#endif

#endif //__SYS_MON_H__
