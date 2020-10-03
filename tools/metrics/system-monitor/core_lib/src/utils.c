#include "utils.h"

unsigned long get_current_time(TimeUnit type)
{
	struct timeval tv;

	gettimeofday(&tv, NULL);
	switch (type) {
	case SEC:
		return tv.tv_sec * 1000;
	case MSEC:
		return tv.tv_sec * 1000 + tv.tv_usec / 1000;
	case USEC:
		return tv.tv_sec * 1000000 + tv.tv_usec;
	default:
		return tv.tv_sec * 1000 + tv.tv_usec / 1000;
	}
}
