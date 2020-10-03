#ifndef __UTILS_H__
#define __UTILS_H__

#include <stddef.h>
#include <sys/time.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum TimeUnit { SEC, MSEC, USEC } TimeUnit;

unsigned long get_current_time(TimeUnit type);

#ifdef __cplusplus
}
#endif

#endif //__UTILS_H__
