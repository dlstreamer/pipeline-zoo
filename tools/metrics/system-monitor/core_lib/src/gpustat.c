#include "gpustat.h"
#include <stdio.h>
#include <sys/types.h>
#include <dirent.h>
#include <stdint.h>
#include <assert.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <inttypes.h>
#include <sys/ioctl.h>
#include <errno.h>
#include <math.h>
#include <locale.h>

#include "igt_perf.h"

struct pmu_pair {
	uint64_t cur;
	uint64_t prev;
};

struct pmu_counter {
	bool present;
	uint64_t config;
	unsigned int idx;
	struct pmu_pair val;
};

struct engine {
	const char *name;
	const char *display_name;

	unsigned int class;
	unsigned int instance;

	unsigned int num_counters;

	struct pmu_counter busy;
	struct pmu_counter wait;
	struct pmu_counter sema;
};

struct engines {
	unsigned int num_engines;
	unsigned int num_counters;
	DIR *root;
	int fd;
	struct pmu_pair ts;

	int imc_fd;
	double imc_reads_scale;
	const char *imc_reads_unit;
	double imc_writes_scale;
	const char *imc_writes_unit;

	struct pmu_counter freq_req;
	struct pmu_counter freq_act;
	struct pmu_counter irq;
	struct pmu_counter rc6;
	struct pmu_counter imc_reads;
	struct pmu_counter imc_writes;

	struct engine engine;
};

static uint64_t get_pmu_config(int dirfd, const char *name, const char *counter)
{
	char buf[128], *p;
	int fd, ret;

	ret = snprintf(buf, sizeof(buf), "%s-%s", name, counter);
	if (ret < 0 || ret == sizeof(buf))
		return -1;

	fd = openat(dirfd, buf, O_RDONLY);
	if (fd < 0)
		return -1;

	ret = read(fd, buf, sizeof(buf));
	close(fd);
	if (ret <= 0)
		return -1;

	p = index(buf, '0');
	if (!p)
		return -1;

	return strtoul(p, NULL, 0);
}

#define engine_ptr(engines, n) (&engines->engine + (n))

static const char *class_display_name(unsigned int class)
{
	switch (class) {
	case I915_ENGINE_CLASS_RENDER:
		return "Render/3D";
	case I915_ENGINE_CLASS_COPY:
		return "Blitter";
	case I915_ENGINE_CLASS_VIDEO:
		return "Video";
	case I915_ENGINE_CLASS_VIDEO_ENHANCE:
		return "VideoEnhance";
	default:
		return "[unknown]";
	}
}

static int engine_cmp(const void *__a, const void *__b)
{
	const struct engine *a = (struct engine *)__a;
	const struct engine *b = (struct engine *)__b;

	if (a->class != b->class)
		return a->class - b->class;
	else
		return a->instance - b->instance;
}

static struct engines *discover_engines(void)
{
	const char *sysfs_root = "/sys/devices/i915/events";
	struct engines *engines;
	struct dirent *dent;
	int ret = 0;
	DIR *d;

	engines = malloc(sizeof(struct engines));
	if (!engines)
		return NULL;

	memset(engines, 0, sizeof(*engines));

	engines->num_engines = 0;

	d = opendir(sysfs_root);
	if (!d)
		return NULL;

	while ((dent = readdir(d)) != NULL) {
		const char *endswith = "-busy";
		const unsigned int endlen = strlen(endswith);
		struct engine *engine = engine_ptr(engines, engines->num_engines);
		char buf[256];

		if (dent->d_type != DT_REG)
			continue;

		if (strlen(dent->d_name) >= sizeof(buf)) {
			ret = ENAMETOOLONG;
			break;
		}

		strcpy(buf, dent->d_name);

		/* xxxN-busy */
		if (strlen(buf) < (endlen + 4))
			continue;
		if (strcmp(&buf[strlen(buf) - endlen], endswith))
			continue;

		memset(engine, 0, sizeof(*engine));

		buf[strlen(buf) - endlen] = 0;
		engine->name = strdup(buf);
		if (!engine->name) {
			ret = errno;
			break;
		}

		engine->busy.config = get_pmu_config(dirfd(d), engine->name, "busy");
		if (engine->busy.config == -1) {
			ret = ENOENT;
			break;
		}

		engine->class = (engine->busy.config & (__I915_PMU_OTHER(0) - 1)) >> I915_PMU_CLASS_SHIFT;

		engine->instance =
			(engine->busy.config >> I915_PMU_SAMPLE_BITS) & ((1 << I915_PMU_SAMPLE_INSTANCE_BITS) - 1);

		ret = snprintf(buf, sizeof(buf), "%s-%u", class_display_name(engine->class), engine->instance);
		if (ret < 0 || ret == sizeof(buf)) {
			ret = ENOBUFS;
			break;
		}
		ret = 0;

		engine->display_name = strdup(buf);
		if (!engine->display_name) {
			ret = errno;
			break;
		}

		engines->num_engines++;
		engines = realloc(engines, sizeof(struct engines) + engines->num_engines * sizeof(struct engine));
		if (!engines) {
			ret = errno;
			break;
		}
	}

	if (ret) {
		free(engines);
		errno = ret;

		return NULL;
	}

	qsort(engine_ptr(engines, 0), engines->num_engines, sizeof(struct engine), engine_cmp);

	engines->root = d;

	return engines;
}

static int filename_to_buf(const char *filename, char *buf, unsigned int bufsize)
{
	int fd, err;
	ssize_t ret;

	fd = open(filename, O_RDONLY);
	if (fd < 0)
		return -1;

	ret = read(fd, buf, bufsize - 1);
	err = errno;
	close(fd);
	if (ret < 1) {
		errno = ret < 0 ? err : ENOMSG;

		return -1;
	}

	if (ret > 1 && buf[ret - 1] == '\n')
		buf[ret - 1] = '\0';
	else
		buf[ret] = '\0';

	return 0;
}

static uint64_t filename_to_u64(const char *filename, int base)
{
	char buf[64], *b;

	if (filename_to_buf(filename, buf, sizeof(buf)))
		return 0;

	b = buf;
	while (*b && !isdigit(*b))
		b++;

	return strtoull(b, NULL, base);
}

static double filename_to_double(const char *filename)
{
	char *oldlocale;
	char buf[80];
	double v;

	if (filename_to_buf(filename, buf, sizeof(buf)))
		return 0;

	oldlocale = setlocale(LC_ALL, "C");
	v = strtod(buf, NULL);
	setlocale(LC_ALL, oldlocale);

	return v;
}

#define IMC_ROOT "/sys/devices/uncore_imc/"
#define IMC_EVENT "/sys/devices/uncore_imc/events/"

static uint64_t imc_type_id(void)
{
	return filename_to_u64(IMC_ROOT "type", 10);
}

static uint64_t imc_data_reads(void)
{
	return filename_to_u64(IMC_EVENT "data_reads", 0);
}

static double imc_data_reads_scale(void)
{
	return filename_to_double(IMC_EVENT "data_reads.scale");
}

static const char *imc_data_reads_unit(void)
{
	char buf[32];

	if (filename_to_buf(IMC_EVENT "data_reads.unit", buf, sizeof(buf)) == 0)
		return strdup(buf);
	else
		return NULL;
}

static uint64_t imc_data_writes(void)
{
	return filename_to_u64(IMC_EVENT "data_writes", 0);
}

static double imc_data_writes_scale(void)
{
	return filename_to_double(IMC_EVENT "data_writes.scale");
}

static const char *imc_data_writes_unit(void)
{
	char buf[32];

	if (filename_to_buf(IMC_EVENT "data_writes.unit", buf, sizeof(buf)) == 0)
		return strdup(buf);
	else
		return NULL;
}

#define _open_pmu(cnt, pmu, fd)                                                                                        \
	({                                                                                                             \
		int fd__;                                                                                              \
                                                                                                                       \
		fd__ = perf_i915_open_group((pmu)->config, (fd));                                                      \
		if (fd__ >= 0) {                                                                                       \
			if ((fd) == -1)                                                                                \
				(fd) = fd__;                                                                           \
			(pmu)->present = true;                                                                         \
			(pmu)->idx = (cnt)++;                                                                          \
		}                                                                                                      \
                                                                                                                       \
		fd__;                                                                                                  \
	})

#define _open_imc(cnt, pmu, fd)                                                                                        \
	({                                                                                                             \
		int fd__;                                                                                              \
                                                                                                                       \
		fd__ = igt_perf_open_group(imc_type_id(), (pmu)->config, (fd));                                        \
		if (fd__ >= 0) {                                                                                       \
			if ((fd) == -1)                                                                                \
				(fd) = fd__;                                                                           \
			(pmu)->present = true;                                                                         \
			(pmu)->idx = (cnt)++;                                                                          \
		}                                                                                                      \
                                                                                                                       \
		fd__;                                                                                                  \
	})

static int pmu_init(struct engines *engines)
{
	unsigned int i;
	int fd;

	engines->fd = -1;
	engines->num_counters = 0;

	engines->irq.config = I915_PMU_INTERRUPTS;
	fd = _open_pmu(engines->num_counters, &engines->irq, engines->fd);
	if (fd < 0)
		return -1;

	engines->freq_req.config = I915_PMU_REQUESTED_FREQUENCY;
	_open_pmu(engines->num_counters, &engines->freq_req, engines->fd);

	engines->freq_act.config = I915_PMU_ACTUAL_FREQUENCY;
	_open_pmu(engines->num_counters, &engines->freq_act, engines->fd);

	engines->rc6.config = I915_PMU_RC6_RESIDENCY;
	_open_pmu(engines->num_counters, &engines->rc6, engines->fd);

	for (i = 0; i < engines->num_engines; i++) {
		struct engine *engine = engine_ptr(engines, i);
		struct {
			struct pmu_counter *pmu;
			const char *counter;
		} *cnt, counters[] = {
			{ .pmu = &engine->busy, .counter = "busy" },
			{ .pmu = &engine->wait, .counter = "wait" },
			{ .pmu = &engine->sema, .counter = "sema" },
			{ .pmu = NULL, .counter = NULL },
		};

		for (cnt = counters; cnt->pmu; cnt++) {
			if (!cnt->pmu->config)
				cnt->pmu->config = get_pmu_config(dirfd(engines->root), engine->name, cnt->counter);
			fd = _open_pmu(engines->num_counters, cnt->pmu, engines->fd);
			if (fd >= 0)
				engine->num_counters++;
		}
	}

	engines->imc_fd = -1;
	if (imc_type_id()) {
		unsigned int num = 0;

		engines->imc_reads_scale = imc_data_reads_scale();
		engines->imc_writes_scale = imc_data_writes_scale();

		engines->imc_reads_unit = imc_data_reads_unit();
		if (!engines->imc_reads_unit)
			return -1;

		engines->imc_writes_unit = imc_data_writes_unit();
		if (!engines->imc_writes_unit)
			return -1;

		engines->imc_reads.config = imc_data_reads();
		if (!engines->imc_reads.config)
			return -1;

		engines->imc_writes.config = imc_data_writes();
		if (!engines->imc_writes.config)
			return -1;

		fd = _open_imc(num, &engines->imc_reads, engines->imc_fd);
		if (fd < 0)
			return -1;
		fd = _open_imc(num, &engines->imc_writes, engines->imc_fd);
		if (fd < 0)
			return -1;

		engines->imc_reads.present = true;
		engines->imc_writes.present = true;
	}

	return 0;
}

static uint64_t pmu_read_multi(int fd, unsigned int num, uint64_t *val)
{
	uint64_t buf[2 + num];
	unsigned int i;
	ssize_t len;

	memset(buf, 0, sizeof(buf));

	len = read(fd, buf, sizeof(buf));
	assert(len == sizeof(buf));

	for (i = 0; i < num; i++)
		val[i] = buf[2 + i];

	return buf[1];
}

static double __pmu_calc(struct pmu_pair *p, double d, double t, double s)
{
	double v;

	v = p->cur - p->prev;
	v /= d;
	v /= t;
	v *= s;

	if (s == 100.0 && v > 100.0)
		v = 100.0;

	return v;
}

static void fill_str(char *buf, unsigned int bufsz, char c, unsigned int num)
{
	unsigned int i;

	for (i = 0; i < num && i < (bufsz - 1); i++)
		*buf++ = c;

	*buf = 0;
}

static void pmu_calc(struct pmu_counter *cnt, char *buf, unsigned int bufsz, unsigned int width, unsigned int width_dec,
		     double d, double t, double s)
{
	double val;
	int len;

	assert(bufsz >= (width + width_dec + 1));

	if (!cnt->present) {
		fill_str(buf, bufsz, '-', width + width_dec);
		return;
	}

	val = __pmu_calc(&cnt->val, d, t, s);

	len = snprintf(buf, bufsz, "%*.*f", width + width_dec, width_dec, val);
	if (len < 0 || len == bufsz) {
		fill_str(buf, bufsz, 'X', width + width_dec);
		return;
	}
}

static uint64_t __pmu_read_single(int fd, uint64_t *ts)
{
	uint64_t data[2] = {};
	ssize_t len;

	len = read(fd, data, sizeof(data));
	assert(len == sizeof(data));

	if (ts)
		*ts = data[1];

	return data[0];
}

static uint64_t pmu_read_single(int fd)
{
	return __pmu_read_single(fd, NULL);
}

static void __update_sample(struct pmu_counter *counter, uint64_t val)
{
	counter->val.prev = counter->val.cur;
	counter->val.cur = val;
}

static void update_sample(struct pmu_counter *counter, uint64_t *val)
{
	if (counter->present)
		__update_sample(counter, val[counter->idx]);
}

static void pmu_sample(struct engines *engines)
{
	const int num_val = engines->num_counters;
	uint64_t val[2 + num_val];
	unsigned int i;

	engines->ts.prev = engines->ts.cur;

	if (engines->imc_fd >= 0) {
		pmu_read_multi(engines->imc_fd, 2, val);
		update_sample(&engines->imc_reads, val);
		update_sample(&engines->imc_writes, val);
	}

	engines->ts.cur = pmu_read_multi(engines->fd, num_val, val);

	update_sample(&engines->freq_req, val);
	update_sample(&engines->freq_act, val);
	update_sample(&engines->irq, val);
	update_sample(&engines->rc6, val);

	for (i = 0; i < engines->num_engines; i++) {
		struct engine *engine = engine_ptr(engines, i);

		update_sample(&engine->busy, val);
		update_sample(&engine->sema, val);
		update_sample(&engine->wait, val);
	}
}

void gst_ru_gpu_init(struct GstGPUStatInterim *gpu_stat_ref)
{
	struct engines *engines;
	unsigned int i;
	int ret, ch;

	if (!gpu_stat_ref)
		return;

	memset(gpu_stat_ref, 0, sizeof(struct GstGPUStatInterim));

	engines = discover_engines();
	if (!engines) {
		printf("Failed to detect engines! (Kernel 4.16 or newer is required for i915 PMU support.)\n");
		return;
	}

	ret = pmu_init(engines);
	if (ret) {
		printf("Failed to initialize PMU!\n");
		free(engines);
		return;
	}

	gpu_stat_ref->engines = engines;
	gpu_stat_ref->isFirstTime = 1; //TRUE;
}

void gst_ru_gpu_compute(struct GstGPUStatInterim *gpu_stat_ref)
{
	int i;
	double t;
	struct engines *engines;

	if (!gpu_stat_ref)
		return;

	engines = (struct engines *)gpu_stat_ref->engines;
	if (!engines)
		return;

	if (gpu_stat_ref->isFirstTime) {
		pmu_sample(engines);
		gpu_stat_ref->isFirstTime = false;
	}

	pmu_sample(engines);

	/* parse data*/
	t = (double)(engines->ts.cur - engines->ts.prev) / 1e9;

	gpu_stat_ref->freq_req = __pmu_calc(&engines->freq_req.val, 1.0, t, 1);
	gpu_stat_ref->freq_act = __pmu_calc(&engines->freq_act.val, 1.0, t, 1);
	gpu_stat_ref->irq = __pmu_calc(&engines->irq.val, 1.0, t, 1);
	gpu_stat_ref->rc6 = __pmu_calc(&engines->rc6.val, 1e9, t, 100);

	if (engines->imc_reads.present) {
		gpu_stat_ref->imc_reads = __pmu_calc(&engines->imc_reads.val, 1.0, t, engines->imc_reads_scale);
		gpu_stat_ref->imc_writes = __pmu_calc(&engines->imc_writes.val, 1.0, t, engines->imc_writes_scale);
	} else {
		gpu_stat_ref->imc_reads = 0.;
		gpu_stat_ref->imc_writes = 0.;
	}

	for (i = 0; i < engines->num_engines; i++) {
		struct engine *engine = engine_ptr(engines, i);

		if (!engine->num_counters)
			continue;

		gpu_stat_ref->blocks[i].dispName = engine->display_name;

		if (gpu_stat_ref->blocks[i].dispName) {
			gpu_stat_ref->blocks[i].sema = __pmu_calc(&engine->sema.val, 1e9, t, 100);
			gpu_stat_ref->blocks[i].wait = __pmu_calc(&engine->wait.val, 1e9, t, 100);
			gpu_stat_ref->blocks[i].busy = __pmu_calc(&engine->busy.val, 1e9, t, 100);
		} else {
			gpu_stat_ref->blocks[i].sema = 0.;
			gpu_stat_ref->blocks[i].wait = 0.;
			gpu_stat_ref->blocks[i].busy = 0.;
		}
	}
}
