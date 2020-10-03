
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "papi.h"
#include "cpustat.h"
#include "utils.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/time.h> /* for gettimeofday*/

#define CPU_NAME_MAX_SIZE 8
#define S(arg) XS(arg)
#define XS(arg) #arg

#define LOG_MSG_WITH_ARGS(STR, ...) printf("%s:%d: " #STR "\n", __FILE__, __LINE__, __VA_ARGS__)

#define LOG_MSG(STR) printf("%s:%d: " #STR "\n", __FILE__, __LINE__)

#define CPU_FREQUENCY_CMD "grep MHz /proc/cpuinfo"
#define CPU_NUM_FROM_PROC_CPUINFO CPU_FREQUENCY_CMD " | wc -l"

static void init_cpu_frequency(struct GstCPUStatInterim *cpu_stat_ref)
{
	int cpuinfo_cpu_num;
	int read_positions;
	FILE *cmd = NULL;

	cpu_stat_ref->cpu_frequency = NULL;
	cpu_stat_ref->cpu_frequency_available = false;

	if (cpu_stat_ref->cpu_num < 1) {
		LOG_MSG_WITH_ARGS("CPU frequency is unavailable: Invalid CPU number: %d", cpu_stat_ref->cpu_num);
		goto failed;
	}

	cmd = popen(CPU_NUM_FROM_PROC_CPUINFO, "r");
	if (cmd == NULL) {
		LOG_MSG_WITH_ARGS("CPU frequency is unavailable: Failed to read /proc/cpuinfo with command %s",
				  CPU_NUM_FROM_PROC_CPUINFO);
		goto failed;
	}

	read_positions = fscanf(cmd, "%d", &cpuinfo_cpu_num);
	pclose(cmd);

	if (read_positions < 1) {
		LOG_MSG("CPU frequency is unavailable: Failed to get cpu number from /proc/cpuinfo");
		goto failed;
	}

	if (cpuinfo_cpu_num != cpu_stat_ref->cpu_num) {
		LOG_MSG_WITH_ARGS(
			"CPU frequency is unavailable: CPU number from /proc/cpuinfo is different. Expected %d - Actual %d",
			cpu_stat_ref->cpu_num, cpuinfo_cpu_num);
		goto failed;
	}

	cpu_stat_ref->cpu_frequency_available = true;
	cpu_stat_ref->cpu_frequency = (float *)malloc(sizeof(float) * cpuinfo_cpu_num);
	if (cpu_stat_ref->cpu_frequency == 0)
		cpu_stat_ref->cpu_frequency_available = false;
failed:
	return;
}

static void read_cpu_memory(struct GstCPUStatInterim *cpu_stat_ref)
{
	FILE *fd;
	int ret;
	unsigned long memtotal;
	unsigned long memfree;
	unsigned long memavble;    

    fd = fopen("/proc/meminfo", "r");
	if (fd == NULL) {
		LOG_MSG("/proc/meminfo file could not be opened");
	}
    
    ret = fscanf(fd, "MemTotal: %ld kB\n", &memtotal);
    ret = fscanf(fd, "MemFree: %ld kB\n", &memfree);
	ret = fscanf(fd, "MemAvailable: %ld kB\n", &memavble);

    cpu_stat_ref->mem_total = memtotal;
	cpu_stat_ref->mem_free = memfree;
    cpu_stat_ref->mem_used = memtotal - memfree;
    
    fclose(fd);

}

static void read_cpu_frequency(struct GstCPUStatInterim *cpu_stat_ref)
{
	if (!cpu_stat_ref->cpu_frequency_available)
		return;

	char *buff = NULL;
	size_t length = 0;
	int cpu_id = 0;

	FILE *cmd = popen(CPU_FREQUENCY_CMD, "r");

	if (cmd == NULL) {
		LOG_MSG_WITH_ARGS("Failed to read CPU frequency from /proc/cpuinfo with command %s", CPU_FREQUENCY_CMD);
		goto failed;
	}

	while (getline(&buff, &length, cmd) != -1) {
		if (cpu_id >= cpu_stat_ref->cpu_num) {
			LOG_MSG_WITH_ARGS("Number of CPUs in /proc/cpuinfo is more than expected (%d).",
					  cpu_stat_ref->cpu_num);
			goto failed;
		}
		float core_freq = 0.f;

		if (sscanf(buff, "%*[^:]: %f", &core_freq) != 1) {
			LOG_MSG_WITH_ARGS("Failed to parse core frequency from line: %s", buff);
			goto failed;
		}
		cpu_stat_ref->cpu_frequency[cpu_id] = core_freq;
		cpu_id++;
	}
	if (cpu_id < cpu_stat_ref->cpu_num - 1) {
		LOG_MSG_WITH_ARGS("Number of CPUs in /proc/cpuinfo - %d is less than expected - %d", cpu_id,
				  cpu_stat_ref->cpu_num);
		goto failed;
	}

	goto normal_exit;

failed:
	LOG_MSG("CPU frequency is unavailable");
	cpu_stat_ref->cpu_frequency_available = false;
	free(cpu_stat_ref->cpu_frequency);
	cpu_stat_ref->cpu_frequency = NULL;

normal_exit:
	free(buff);
	pclose(cmd);
}

void gst_ru_cpu_init(struct GstCPUStatInterim *cpu_stat_ref)
{
	int cpu_num = 0;

	if (!cpu_stat_ref)
		return;
	memset(cpu_stat_ref, 0, sizeof(GstCPUStatInterim));
	cpu_stat_ref->cpu_array_sel = false;
	cpu_num = sysconf(_SC_NPROCESSORS_CONF);
	if (cpu_num == -1) {
		printf("failed to get number of cpus\n");
		cpu_num = 1;
	}
	cpu_stat_ref->cpu_load = (float *)malloc(cpu_num * sizeof(float));
	cpu_stat_ref->user = (int *)malloc(8 * cpu_num * sizeof(int));

	cpu_stat_ref->user_aux = cpu_stat_ref->user + cpu_num;
	cpu_stat_ref->nice = cpu_stat_ref->user_aux + cpu_num;
	cpu_stat_ref->nice_aux = cpu_stat_ref->nice + cpu_num;
	cpu_stat_ref->system = cpu_stat_ref->nice_aux + cpu_num;
	cpu_stat_ref->system_aux = cpu_stat_ref->system + cpu_num;
	cpu_stat_ref->idle = cpu_stat_ref->system_aux + cpu_num;
	cpu_stat_ref->idle_aux = cpu_stat_ref->idle + cpu_num;

	cpu_stat_ref->cpu_num = cpu_num;

	init_cpu_frequency(cpu_stat_ref);
}

void gst_ru_cpu_finalize(struct GstCPUStatInterim *cpu_stat_ref)
{
	free(cpu_stat_ref->cpu_load);
	free(cpu_stat_ref->user);

	cpu_stat_ref->cpu_num = 0;
}

#define LOG_FILE "/temp/results/system_monitor.err"

void gst_ru_cpu_compute(struct GstCPUStatInterim *cpu_stat_ref)
{
	float *cpu_load;
	int cpu_num;
	int cpu_id;
	FILE *fd;

	int *user;
	int *user_aux;
	int *nice;
	int *nice_aux;
	int *system;
	int *system_aux;
	int *idle;
	int *idle_aux;

	char cpu_name[CPU_NAME_MAX_SIZE];
	int iowait; /* Time waiting for I/O to complete */
	int irq; /* Time servicing interrupts        */
	int softirq; /* Time servicing softirqs          */
	int steal; /* Time spent in other OSes when in virtualized env */
	int quest; /* Time spent running a virtual CPU for guest OS    */
	int quest_nice; /* Time spent running niced guest */
	float num_value;
	float den_value;
	bool cpu_array_sel;
	int ret;

	if (!cpu_stat_ref)
		return;

	user = cpu_stat_ref->user;
	user_aux = cpu_stat_ref->user_aux;
	nice = cpu_stat_ref->nice;
	nice_aux = cpu_stat_ref->nice_aux;
	system = cpu_stat_ref->system;
	system_aux = cpu_stat_ref->system_aux;
	idle = cpu_stat_ref->idle;
	idle_aux = cpu_stat_ref->idle_aux;

	cpu_array_sel = cpu_stat_ref->cpu_array_sel;
	cpu_load = cpu_stat_ref->cpu_load;
	cpu_num = cpu_stat_ref->cpu_num;
	/* Compute the load for each core */
	fd = fopen("/proc/stat", "r");
	if (cpu_array_sel == 0) {
		ret = fscanf(fd, "%" S(CPU_NAME_MAX_SIZE) "s %d %d %d %d %d %d %d %d %d %d", cpu_name, &user[0],
			     &nice[0], &system[0], &idle[0], &iowait, &irq, &softirq, &steal, &quest, &quest_nice);
		for (cpu_id = 0; cpu_id < cpu_num; ++cpu_id) {
			ret = fscanf(fd, "%" S(CPU_NAME_MAX_SIZE) "s %d %d %d %d %d %d %d %d %d %d", cpu_name,
				     &user[cpu_id], &nice[cpu_id], &system[cpu_id], &idle[cpu_id], &iowait, &irq,
				     &softirq, &steal, &quest, &quest_nice);
		}
		/* Compute the utilization for each core */
		for (cpu_id = 0; cpu_id < cpu_num; ++cpu_id) {
			num_value = ((user[cpu_id] + nice[cpu_id] + system[cpu_id]) -
				     (user_aux[cpu_id] + nice_aux[cpu_id] + system_aux[cpu_id]));
			den_value = ((user[cpu_id] + nice[cpu_id] + system[cpu_id] + idle[cpu_id]) -
				     (user_aux[cpu_id] + nice_aux[cpu_id] + system_aux[cpu_id] + idle_aux[cpu_id]));

			/*Buggy situation. lets log out state.*/
			if (den_value == 0) {
				FILE *f_err = NULL;

				f_err = fopen(LOG_FILE, "at");
				if (f_err) {
					fprintf(f_err, "current: CPU=%d %d %d %d %d %d %d %d %d %d %d\n", cpu_id,
						user[0], nice[0], system[0], idle[0], iowait, irq, softirq, steal,
						quest, quest_nice);
					fprintf(f_err, "history: CPU=%d %d %d %d %d\n", cpu_id, user_aux[0],
						nice_aux[0], system_aux[0], idle_aux[0]);
					fprintf(f_err, "========================\n");
					fclose(f_err);
				}
			}
			cpu_load[cpu_id] = 100 * (num_value / den_value);
		}
		cpu_array_sel = 1;
	} else {
		ret = fscanf(fd, "%" S(CPU_NAME_MAX_SIZE) "s %d %d %d %d %d %d %d %d %d %d", cpu_name, &user_aux[0],
			     &nice_aux[0], &system_aux[0], &idle_aux[0], &iowait, &irq, &softirq, &steal, &quest,
			     &quest_nice);
		for (cpu_id = 0; cpu_id < cpu_num; ++cpu_id) {
			ret = fscanf(fd, "%" S(CPU_NAME_MAX_SIZE) "s %d %d %d %d %d %d %d %d %d %d", cpu_name,
				     &user_aux[cpu_id], &nice_aux[cpu_id], &system_aux[cpu_id], &idle_aux[cpu_id],
				     &iowait, &irq, &softirq, &steal, &quest, &quest_nice);
		}
		/* Compute the utilization for each core */
		for (cpu_id = 0; cpu_id < cpu_num; ++cpu_id) {
			num_value = ((user_aux[cpu_id] + nice_aux[cpu_id] + system_aux[cpu_id]) -
				     (user[cpu_id] + nice[cpu_id] + system[cpu_id]));
			den_value = ((user_aux[cpu_id] + nice_aux[cpu_id] + system_aux[cpu_id] + idle_aux[cpu_id]) -
				     (user[cpu_id] + nice[cpu_id] + system[cpu_id] + idle[cpu_id]));
			/*Buggy situation. lets log out state.*/
			if (den_value == 0) {
				FILE *f_err = NULL;

				f_err = fopen(LOG_FILE, "at");
				if (f_err) {
					fprintf(f_err, "current: CPU=%d %d %d %d %d %d %d %d %d %d %d\n", cpu_id,
						user_aux[0], nice_aux[0], system_aux[0], idle_aux[0], iowait, irq,
						softirq, steal, quest, quest_nice);
					fprintf(f_err, "history: CPU=%d %d %d %d %d\n", cpu_id, user[0], nice[0],
						system[0], idle[0]);
					fprintf(f_err, "========================\n");
					fclose(f_err);
				}
			}
			cpu_load[cpu_id] = 100 * (num_value / den_value);
		}
		cpu_array_sel = 0;
	}

	cpu_stat_ref->cpu_array_sel = cpu_array_sel;
	fclose(fd);

	read_cpu_frequency(cpu_stat_ref);
	read_cpu_memory(cpu_stat_ref);
}
