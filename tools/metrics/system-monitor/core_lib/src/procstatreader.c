#include "procstatreader.h"
#include "utils.h"
#include <error.h>
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

enum ProcStatItems { PID = 0, MINFLT = 9, MAJFLT = 11 };

enum ProcStatReaderErrors try_read_page_faults(struct GstProcStatInterim *proc_stat, const int pid);
enum ProcStatReaderErrors try_read_process_status(struct GstProcStatInterim *proc_stat, const int pid);

static unsigned int Inc(unsigned int offset)
{
	unsigned int n;

	n = (offset + 1) & 0x1; /*increment by module 2*/
	return n;
}

enum ProcStatReaderErrors gst_ru_proc_stat_read(struct GstProcStatInterim *proc_stat, int pid)
{
	enum ProcStatReaderErrors status = SUCCESS;

	if (proc_stat == NULL) {
		// how do we log errors?
		return INVALID_ARGUMENTS;
	}

	if (pid == 0) {
		status = INVALID_ARGUMENTS;
		goto EXIT;
	}

	status = try_read_page_faults(proc_stat, pid);
	if (status != SUCCESS)
		goto EXIT;

	status = try_read_process_status(proc_stat, pid);
	if (status != SUCCESS)
		goto EXIT;

	/* Move counters history position*/
	proc_stat->history.offset = Inc(proc_stat->history.offset);

EXIT:
	return status;
}

const char *gst_ru_proc_stat_error_message(enum ProcStatReaderErrors error_code)
{
	switch (error_code) {
	case SUCCESS:
		return "No error";
	case PROCESS_NOT_FOUND:
		return "Process not found";
	case INVALID_ARGUMENTS:
		return "Invalid arguments";
	default:
	case UNEXPECTED_ERROR:
		return "Unexpected error happened";
	}
}

#define MAX_WORDS 1024
struct word {
	const char *name;
	unsigned int len;
};

struct book {
	struct word words[1024];
	unsigned int len;
};

static void split_by_spaces(const char *str, struct book *words)
{
	const char *ptr = str;
	unsigned int i = 0;
	bool inword = false;
	unsigned int len = 1;

	if (words == 0)
		return;

	while (*ptr != '\0') {
		if ((*ptr == ' ') || (*ptr == '\t')) {
			if (inword)
				words->words[i].len = len;
			len = 1;
			inword = false;
			i++;
			goto CONT;
		}
		if (inword)
			len++;
		else {
			words->words[i].name = ptr;
			inword = true;
		}
CONT:
		if (i > MAX_WORDS)
			break;
		ptr++;
	}

	if (inword) {
		words->words[i].len = len;
		i++;
	}

	words->len = i;
}

static bool isEqual(const char *str, struct word *w)
{
	bool status = true;
	int i;
	const char *ptr1;
	const char *ptr2;

	if (!str || !w) {
		status = false;
		goto EXIT;
	}

	if (strlen(str) != w->len) {
		status = false;
		goto EXIT;
	}

	ptr1 = str;
	ptr2 = w->name;
	if (!ptr2) {
		status = false;
		goto EXIT;
	}

	for (i = 0; i < w->len; i++, ptr1++, ptr2++) {
		if (*ptr1 != *ptr2) {
			status = false;
			break;
		}
	}

EXIT:
	return status;
}

static void clean_book(struct book *words)
{
	words->len = 0;
}

static void print_book(struct book *words)
{
	unsigned int i;

	for (i = 0; i < words->len; i++)
		printf("%d: %s[%d]\n", i, words->words[i].name, words->words[i].len);
}

#define CURR_VAL_POS (proc_stat->history.offset)
#define PREV_VAL_POS (Inc(proc_stat->history.offset))

enum ProcStatReaderErrors try_read_page_faults(struct GstProcStatInterim *proc_stat, const int pid)
{
	struct book b;
	unsigned int booksize = 0;
	char *path = NULL;
	char *line = NULL;
	FILE *f_in = NULL;
	size_t len = 0;
	ssize_t read;
	enum ProcStatReaderErrors status = SUCCESS;

	asprintf(&path, "/proc/%d/stat", pid);
	if (path == NULL) {
		status = UNEXPECTED_ERROR;
		goto EXIT;
	}

	f_in = fopen(path, "rt");
	if (f_in == NULL) {
		status = PROCESS_NOT_FOUND;
		goto EXIT;
	}

	if (-1 == getline(&line, &len, f_in)) {
		status = UNEXPECTED_ERROR;
		goto EXIT;
	}

	split_by_spaces(line, &b);

	/* Read current counter value*/
	proc_stat->history.hminflt[CURR_VAL_POS] = strtoul(b.words[MINFLT].name, 0, 10);
	proc_stat->history.hmajflt[CURR_VAL_POS] = strtoul(b.words[MAJFLT].name, 0, 10);

	/* Substruct last read value from previously collected to report delta as metric output*/
	proc_stat->minflt = proc_stat->history.hminflt[CURR_VAL_POS] - proc_stat->history.hminflt[PREV_VAL_POS];
	proc_stat->majflt = proc_stat->history.hmajflt[CURR_VAL_POS] - proc_stat->history.hmajflt[PREV_VAL_POS];
EXIT:
	if (f_in)
		fclose(f_in);
	free(line);
	free(path);
	return status;
}

enum ProcStatReaderErrors try_read_process_status(struct GstProcStatInterim *proc_stat, const int pid)
{
	char *path = NULL;
	char *line = NULL;
	FILE *f_in = NULL;
	size_t len = 0;
	ssize_t read;
	struct book b;
	enum ProcStatReaderErrors status = SUCCESS;

	asprintf(&path, "/proc/%d/status", pid);
	if (path == NULL) {
		status = UNEXPECTED_ERROR;
		goto EXIT;
	}

	f_in = fopen(path, "rt");
	if (f_in == NULL) {
		status = PROCESS_NOT_FOUND;
		goto EXIT;
	}

	while (-1 != getline(&line, &len, f_in)) {
		int features = 0;
		static int max_num_features = 4;

		clean_book(&b);
		split_by_spaces(line, &b);

		if (isEqual("VmRSS:", &b.words[0])) {
			proc_stat->resident_set_size = strtoul(b.words[1].name, 0, 10);
			features++;
		} else if (isEqual("voluntary_ctxt_switches:", &b.words[0])) {
			/* Read current counter value*/
			proc_stat->history.hvoluntary_ctxt_switches[CURR_VAL_POS] =
				strtoul(b.words[b.len - 1].name, 0, 10);
			/* Substruct last read value from previously collected to report delta as metric output*/
			proc_stat->voluntary_ctxt_switches = proc_stat->history.hvoluntary_ctxt_switches[CURR_VAL_POS] -
							     proc_stat->history.hvoluntary_ctxt_switches[PREV_VAL_POS];
			features++;
		} else if (isEqual("nonvoluntary_ctxt_switches:", &b.words[0])) {
			/* Read current counter value*/
			proc_stat->history.hnonvoluntary_ctxt_switches[CURR_VAL_POS] =
				strtoul(b.words[b.len - 1].name, 0, 10);
			/* Substruct last read value from previously collected to report delta as metric output*/
			proc_stat->nonvoluntary_ctxt_switches =
				proc_stat->history.hnonvoluntary_ctxt_switches[CURR_VAL_POS] -
				proc_stat->history.hnonvoluntary_ctxt_switches[PREV_VAL_POS];
			features++;
		} else if (isEqual("Threads:", &b.words[0])) {
			proc_stat->threads = strtoul(b.words[b.len - 1].name, 0, 10);
			features++;
		}
		if (max_num_features == features)
			break;
		free(line);
		line = NULL;
	}

EXIT:
	if (f_in)
		fclose(f_in);
	free(line);
	free(path);
	return status;
}
