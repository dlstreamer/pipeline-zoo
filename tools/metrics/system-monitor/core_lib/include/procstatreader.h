#ifndef PROCSTATREADER_H
#define PROCSTATREADER_H

#ifdef __cplusplus
extern "C" {
#endif

struct procStatHistory {
	unsigned long hminflt[2];
	unsigned long hmajflt[2];
	unsigned long hvoluntary_ctxt_switches[2];
	unsigned long hnonvoluntary_ctxt_switches[2];
	unsigned int offset;
};

struct GstProcStatInterim {
	unsigned long minflt;
	unsigned long majflt;
	unsigned long voluntary_ctxt_switches;
	unsigned long nonvoluntary_ctxt_switches;
	struct procStatHistory history;
	unsigned long resident_set_size;
	unsigned long threads;
};

enum ProcStatReaderErrors {
	SUCCESS = 0,
	UNEXPECTED_ERROR = -1,
	PROCESS_NOT_FOUND = -2,
	INVALID_ARGUMENTS = -3
};

enum ProcStatReaderErrors gst_ru_proc_stat_read(struct GstProcStatInterim *proc_stat, int pid);

const char *gst_ru_proc_stat_error_message(enum ProcStatReaderErrors error_code);

#ifdef __cplusplus
}
#endif

#endif // PROCSTATREADER_H
