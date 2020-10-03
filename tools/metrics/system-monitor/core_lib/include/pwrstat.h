#ifndef __PWR_STAT_H__
#define __PWR_STAT_H__

#ifdef __cplusplus
extern "C" {
#endif

struct PowerConsumptionStat {
	double value;
	const char *name;
};

struct PowerStatInterim {
	/* Length of power consumption array */
	int power_consumption_array_length;
	/* Power comsumption information for available components (CPU. DRAM, SoC, Package0) */
	struct PowerConsumptionStat *power_consumption_array;
	void *raw_values;
};

void init_power_consumption_metrics(struct PowerStatInterim *pwr_stat_ref);
void finalize_power_consumption_metrics(struct PowerStatInterim *pwr_stat_ref);
void fill_cpu_power_consumption(struct PowerStatInterim *pwr_stat_ref);

#ifdef __cplusplus
}
#endif

#endif
