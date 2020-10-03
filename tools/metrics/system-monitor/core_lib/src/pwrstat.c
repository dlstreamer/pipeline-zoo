
#include "papi.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "pwrstat.h"

#define CPU_NAME_MAX_SIZE 8
#define S(arg) XS(arg)
#define XS(arg) #arg

#define LOG_MSG_WITH_ARGS(STR, ...) printf("%s:%d: " #STR "\n", __FILE__, __LINE__, __VA_ARGS__)

#define LOG_MSG(STR) printf("%s:%d: " #STR "\n", __FILE__, __LINE__)

#define PAPI_CHECK(EXPR, RET)                                                                                          \
	if ((RET = EXPR) != PAPI_OK) {                                                                                 \
		LOG_MSG_WITH_ARGS("Failed to exec: " #EXPR "   Error: %s\n", PAPI_strerror(RET));                      \
	}

// Power Unit is 2^-32 Joules
#define POWER_SCALE_UNIT 4294967296
#define NANOSEC_TO_SEC 1.0e9

#define MAX_PWR_COUNTERS 4

static const char *rapl_events_name[MAX_PWR_COUNTERS] = { "rapl::RAPL_ENERGY_CORES:cpu=0",
							  "rapl::RAPL_ENERGY_PKG:cpu=0", "rapl::RAPL_ENERGY_GPU:cpu=0",
							  "rapl::RAPL_ENERGY_PSYS:cpu=0" };

static const char *sys_mon_events_name[MAX_PWR_COUNTERS] = { "power-cpu-watts", "power-pkg-watts", "power-gpu-watts",
							     "power-psys-watts" };

#define IDX_RAPL 0
#define IDX_SM 1

static const char **events_name_map[2] = { rapl_events_name, sys_mon_events_name };

/* Last time in nanoseconds when power consumtion was measured */
long_long power_time_ns = 0;

void init_power_consumption_metrics(struct PowerStatInterim *pwr_stat_ref)
{
	int ret = -1;
	int events_count = 0;
	int events_code[MAX_PWR_COUNTERS];
	int events_idx[MAX_PWR_COUNTERS];
	int i;

	if (PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT) {
		LOG_MSG("Power: Failed to init PAPI library. Version mismatch\n");
		return;
	}
	for (i = 0; i < MAX_PWR_COUNTERS; i++) {
		int event_code = 0;

		ret = PAPI_event_name_to_code(events_name_map[IDX_RAPL][i], &event_code);
		if (ret != PAPI_OK) {
			LOG_MSG_WITH_ARGS("Power: RAPL event %s is unavailable. Error: %s\n",
					  events_name_map[IDX_RAPL][i], PAPI_strerror(ret));
			continue;
		}

		events_code[events_count] = event_code;
		events_idx[events_count] = i;
		events_count++;
	}

	pwr_stat_ref->power_consumption_array = NULL;
	pwr_stat_ref->power_consumption_array_length = events_count;
	if (events_count == 0) {
		LOG_MSG("Power: No RAPL messages are available. Check permissions");
		return;
	}
	PAPI_CHECK(PAPI_start_counters(events_code, events_count), ret)
	power_time_ns = PAPI_get_real_nsec();
	pwr_stat_ref->power_consumption_array = (struct PowerConsumptionStat *)malloc(
		sizeof(struct PowerConsumptionStat) * pwr_stat_ref->power_consumption_array_length);
	if (pwr_stat_ref->power_consumption_array == NULL) {
		LOG_MSG("Power: Malloc failed.");
		return;
	}

	for (i = 0; i < events_count; i++) {
		pwr_stat_ref->power_consumption_array[i] =
			(struct PowerConsumptionStat){ .value = 0, .name = events_name_map[IDX_SM][events_idx[i]] };
	}
	pwr_stat_ref->raw_values =
		(long_long *)malloc(sizeof(long_long) * pwr_stat_ref->power_consumption_array_length);
}

void finalize_power_consumption_metrics(struct PowerStatInterim *pwr_stat_ref)
{
	int ret;

	if (pwr_stat_ref->power_consumption_array_length) {
		PAPI_CHECK(PAPI_stop_counters((long_long *)pwr_stat_ref->raw_values,
					      pwr_stat_ref->power_consumption_array_length),
			   ret)
		free(pwr_stat_ref->power_consumption_array);
		pwr_stat_ref->power_consumption_array_length = 0;
		free(pwr_stat_ref->raw_values);
	}
}

void fill_cpu_power_consumption(struct PowerStatInterim *pwr_stat_ref)
{
	int events_count = pwr_stat_ref->power_consumption_array_length;

	if (events_count == 0)
		return;

	if (pwr_stat_ref->power_consumption_array == NULL) {
		LOG_MSG("Power: Power consumption array is NULL");
		return;
	}

	if (pwr_stat_ref->raw_values) {
		int ret = -1, i;
		double elapsed_time;

		PAPI_CHECK(PAPI_read_counters(pwr_stat_ref->raw_values, events_count), ret)
		long_long current_time_ns = PAPI_get_real_nsec();
		elapsed_time = ((double)(current_time_ns - power_time_ns)) / NANOSEC_TO_SEC;
		power_time_ns = current_time_ns;
		for (i = 0; i < events_count; i++) {
			pwr_stat_ref->power_consumption_array[i].value =
				(double)((long_long *)pwr_stat_ref->raw_values)[i] / POWER_SCALE_UNIT / elapsed_time;
		}
	} else {
		LOG_MSG("Power: Failed to allocated memory for counters.");
	}
}
