# System Monitor

## Requirements
**The monitor requires Linux Kernel at least version v4.16 and root privileges**.

Otherwise, all GPU utilization metrics will report zero values.

Use .sh script for installing kernel v4.16 on Ubuntu 16.04

## Dependencies
```
sudo apt-get install libpapi-dev
```

## Usage examples
As simple test, run script run.sh from one console        
with sudo privileges          
             
-i reporting interval    
-p pid         
-o output file in CSV         

## Metrics
The following metrics collected by the monitor:
1. **CPU:**
     1. Per core average CPU utilization.
     2. Power consumption of CPU (cores, package, psys if available)
2. **GPU:**
     1. GPU frequeny
     2. GPU active frequency
     3. GPU power consumption (if available)
     4. % of time in RC6
     5. IRQ rate per second
     6. IMC read and write rates
     7. HW blocks utilization (%busy, %wait, %sema) for:
           1. Render
           2. Blitter (copying)
           3. Video0
           4. Video1
           5. Video Enhancement
3. **Memory:**
     1. Used memory in MB
     2. Available memory in MB

## ZeroMQ service

To add support for zmq use:
```
sudo apt-get install libzmq3-dev
```

The service collects CPU/GPU usage metrics every second and sends ZeroMQ messages in the format
```
NAME:VALUE
```
to localhost TCP port 5560.
Run the service with root previligies
```
sudo zmq_service/sys_monitor_service
```