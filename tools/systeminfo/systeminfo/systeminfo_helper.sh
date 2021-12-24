#!/bin/sh
echo '=== HARDWARE INFORMATION ==='
echo

echo '--- CPU ---'
sed '/^$/q' /proc/cpuinfo
echo
echo '--- /sys/devices/system/cpu/cpu0/cpufreq/scaling_* ---'
echo "CPU cur:  $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)"
echo "CPU max:  $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)"
echo "CPU min:  $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq)"
echo

echo '--- Memory ---'
grep MemTotal /proc/meminfo
echo

echo '--- GPU ---'
lspci -nn -vvv -d "::0300"
echo

if [ -f /sys/class/drm/card0/gt_min_freq_mhz ]; then
    echo '--- /sys/class/drm/card0/gt* ---'
    echo "GPU max:  $(cat /sys/class/drm/card0/gt_min_freq_mhz)"
    echo "GPU min:  $(cat /sys/class/drm/card0/gt_max_freq_mhz)"
    echo
fi

echo '=== SOFTWARE INFORMATION ==='
echo

echo '--- /proc/version ---'
cat /proc/version
echo

echo '--- /etc/os-release ---'
grep --color=never -E "(NAME|VERSION|ID)" /etc/os-release
echo

echo '--- OpenCL ---'
clinfo | grep --color=never -E "(Platform Name|Platform Vendor|Platform Version|Device Name|Device Vendor|Device OpenCL|Device Type|Driver Version|frequency)"  | sed '/Device Name/s/^/\n/'
echo

echo
echo '=== HARDWARE ==='
echo

echo '--- Motherboard ---'
/usr/sbin/dmidecode --t 1 | grep -E "Manufacturer|Product"
echo

echo '--- BIOS ---'
/usr/sbin/dmidecode --t 0 | grep -E "Vendor|Version"
echo

echo '--- RAM ---'
/usr/sbin/dmidecode --t 17 | grep -E "Size:|Type:|Speed|Manufacturer|Part|Locator" | sed '/Bank/s/^/\n/'
echo

exit 0
