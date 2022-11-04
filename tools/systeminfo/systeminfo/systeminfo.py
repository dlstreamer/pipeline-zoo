#!/usr/bin/env python3

import re
import os
import socket
import platform
import subprocess
import argparse
import json
import yaml
import glob
import distro
import shlex

def empty_string_if_failure(function):
    def new_func(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception:
            return ""
    return new_func


def output_or_fail(command, **kwargs):
    if isinstance(command, str) and not "shell" in kwargs:
        kwargs["shell"] = True
    return subprocess.check_output(command, **kwargs).decode("utf-8").strip()


def output_or_empty(command, **kwargs):
    try:
        return output_or_fail(command, **kwargs)
    except Exception:
        return ""


def read_or_fail(path):
    return open(path, "r").read().strip()


def read_or_empty(path):
    try:
        return open(path, "r").read().strip()
    except Exception:
        return ""


def get_value(pattern, text):
    res = re.search(pattern, text)
    if res:
        return res.group(1)
    return ""


def get_int_value(pattern, text):
    res = re.search(pattern, text)
    if res:
        return int(res.group(1))
    return 0


def parse_memory(slot, num):
    res = re.search(r"Size: (.*) (MB|GB)", slot)
    if res:
        size,data_size = res.group(1), res.group(2)
        coefficient = 1 if data_size == "MB" else 1024
        size = int(size) * coefficient
        return {
            "Slot": int(num),
            "Vendor": get_value(r"Manufacturer: (.*)", slot),
            "Type": get_value(r"Type: (.*)", slot),
            "Speed": get_value(r"Configured Clock Speed: (.*)", slot),
            "Size": "{0} {1}".format(size, data_size),
            "PartNumber": get_value(r"Part Number: (.*)", slot).strip(),
            "Channel": get_value(r"Locator: (.*)", slot)
        }
    return {
        "Slot": int(num),
        "Vendor": "N/A",
        "Type": "N/A",
        "Speed": "N/A",
        "Size": 0,
        "PartNumber": "N/A",
        "Channel": "N/A"
    }


def memory():
    try:
        text = output_or_empty("/usr/sbin/dmidecode -t 17")

        result = []
        slot_counter = 0
        for slot in text.split("Memory Device"):
            num = get_value(r"Bank Locator: BANK (\d+)", slot)

            if (num != ""):
                result.append(parse_memory(slot, num))
            else:
                num = get_value(r"Bank Locator: (.*)", slot)
                if (num != ""):
                    num = str(slot_counter)
                    slot_counter += 1
                    result.append(parse_memory(slot, num))

        return result
    except:
        pass

    try:
        meminfo = read_or_fail("/proc/meminfo")
        memsize = int(re.match(r"MemTotal:\s+(\d+)\s+kB", meminfo).group(1)) // 1024
    except:
        memsize = 0
    return [{"Size (MB)": memsize}]


def os_release():
    text = read_or_fail("/etc/os-release")
    kernel = output_or_empty("uname -r")
    result = {
        "Name": get_value(r"PRETTY_NAME=\"(.*)\"", text),
        "Kernel": kernel
    }
    return result


def bios():
    try:
        text = output_or_empty("/usr/sbin/dmidecode -t 0")
        return {
            "Vendor":  get_value(r".*Vendor:\s*(.*)", text),
            "Version": get_value(r".*Version:\s*(.*)", text),
            "Release": get_value(r".*Release Date:\s*(.*)", text),
        }
    except:
        pass
    return {
        "Vendor": read_or_empty("/sys/class/dmi/id/bios_vendor"),
        "Version": read_or_empty("/sys/class/dmi/id/bios_version"),
        "Release": read_or_empty("/sys/class/dmi/id/bios_date")
    }


def motherboard():
    try:
        text = output_or_empty("/usr/sbin/dmidecode -t 2")
        result = get_value(r".*Manufacturer:\s*(.*)", text) + " / " + get_value(r".*Product\sName:\s*(.*)", text)
        return result
    except:
        pass
    return "{} / {}".format(
        read_or_empty("/sys/devices/virtual/dmi/id/board_vendor"),
        read_or_empty("/sys/devices/virtual/dmi/id/board_name")
    )


def hostname():
    return socket.gethostname()


@empty_string_if_failure
def opencv_version(openvino):
    opencv_path="{}/opencv/cmake".format(openvino)
    text = read_or_fail(os.path.join(opencv_path, "OpenCVConfig-version.cmake"))
    return get_value(r".*set\(OpenCV_VERSION\s*(.*)\)", text)

@empty_string_if_failure
def dlstreamer_version():
    text = output_or_empty("gst-inspect-1.0 gvadetect")
    result = get_value(r".*Version\s*(.*)",text)
    return result

@empty_string_if_failure
def openvino_version(openvino):
    text = output_or_empty(["realpath", openvino])
    result = get_value(r".*openvino_(.*)", text)
    return result


@empty_string_if_failure
def mo_version(openvino):
    version_file = "{}/deployment_tools/model_optimizer/version.txt".format(openvino)
    text = open(version_file, "r").readlines()[-1]
    return text


@empty_string_if_failure
def ie_version(openvino):
    version_file = "{}/deployment_tools/inference_engine/version.txt".format(openvino)
    text = open(version_file, "r").readlines()[-1]
    return text


@empty_string_if_failure
def open_model_zoo_version(omz_path):
    return output_or_empty(["git", "rev-parse", "HEAD"], cwd=omz_path)


@empty_string_if_failure
def model_zoo_version(model_zoo_path):
    return output_or_empty(["git", "rev-parse", "HEAD"], cwd=model_zoo_path)


@empty_string_if_failure
def model_zoo_check_version(model_zoo_path, subpath, no_diff=False):
    if not model_zoo_path:
        return ""
    path_to_check = os.path.join(model_zoo_path, subpath)
    version = output_or_empty(["git", "rev-parse", "HEAD"], cwd=path_to_check)
    if no_diff:
        return version
    diff_with_master = output_or_empty(["git", "diff", "HEAD", "master"], cwd=path_to_check)
    if diff_with_master == "":
        return version + " / master"
    else:
        return version + " / not master"


@empty_string_if_failure
def mxnet_version(mxnet_path="/opt/incubator-mxnet"):
    mkl_version = read_or_fail("/opt/intel/mkl/include/mkl_version.h")
    return output_or_fail(["git", "describe", "--tags", "--abbrev=0"], cwd=mxnet_path) \
        + " / MKL: " + get_value(r".*INTEL_MKL_VERSION\s*(.*)", mkl_version)


@empty_string_if_failure
def caffe2_version(caffe2_path="/opt/caffe2"):
    mkl_version = read_or_fail("/opt/intel/mkl/include/mkl_version.h")
    return output_or_fail(["git", "name-rev", "--name-only", "HEAD"], cwd=caffe2_path) \
        + " / MKL: " + get_value(r".*INTEL_MKL_VERSION\s*(.*)", mkl_version)


@empty_string_if_failure
def intel_caffe_version(ic_path="/opt/intel-caffe"):
    mkl_version = ""
    for file_with_version in glob.glob(os.path.join(ic_path, "external/mkl/mklml*/include/mkl_version.h")):
        mkl_version = read_or_fail(file_with_version)
    text  = output_or_fail(["git", "describe", "--tags", "--abbrev=0"], cwd=ic_path)
    text += " / MKL: " + get_value(r".*INTEL_MKL_VERSION\s*(.*)", mkl_version)
    return text


@empty_string_if_failure
def cntk_version(cntk_path="/opt/cntk"):
    text = output_or_fail(["git", "describe", "--tags", "--abbrev=0"], cwd=os.path.join(cntk_path, "code"))
    try:
        mkl_version = ""
        for file_with_version in glob.glob(os.path.join(cntk_path, "mklml_lnx*/include/mkl_version.h")):
            mkl_version = read_or_fail(file_with_version)
        text += " / MKL: " + get_value(r".*INTEL_MKL_VERSION\s*(.*)", mkl_version)
    except:
        pass
    try:
        protobuf_version = ""
        for file_with_version in glob.glob(os.path.join(cntk_path, "protobuf*/install/lib/pkgconfig/protobuf.pc")):
            protobuf_version = read_or_fail(file_with_version)
        text += " / Protobuf: " + get_value(r".*Version:\s*(.*)", protobuf_version)
    except:
        pass
    return text


@empty_string_if_failure
def tvm_version(tvm_path="/opt/tvm"):
    mkl_version = read_or_fail("/opt/intel/mkl/include/mkl_version.h")
    llvm_version = ""
    for file_with_llvm_version in glob.glob(os.path.join(tvm_path, "llvm/*/lib/cmake/llvm/LLVMConfig.cmake")):
        llvm_version = read_or_fail(file_with_llvm_version)
    text = output_or_fail(["git", "describe", "--tags", "--abbrev=0"], cwd=os.path.join(tvm_path, "code")) + " / MKL: " + get_value(r".*INTEL_MKL_VERSION\s*(.*)", mkl_version) + \
            " / LLVM: " + get_value(r".*LLVM_PACKAGE_VERSION\s*(.*)", llvm_version)[:-1]
    return text


@empty_string_if_failure
def tensorflow_version(tf_path="/opt/tf"):
    bazel_version = open("/opt/bazel/version.txt", "r").readlines()[0].split()[2]
    mkl_version = ""
    for file_with_version in glob.glob("/opt/bazel/tmp/_bazel_root/*/external/mkl_linux/include/mkl_version.h"):
        mkl_version = read_or_fail(file_with_version)
    text = output_or_empty(["git", "describe", "--tags", "--abbrev=0"], cwd=tf_path) + \
            " / Bazel: " + bazel_version + " / MKL: " + get_value(r".*INTEL_MKL_VERSION\s*(.*)", mkl_version) + \
            " [with KMP_BLOCKTIME=0,KMP_AFFINITY=granularity=fine,compact,1,0]"
    return text


@empty_string_if_failure
def ngraph_version(ng_path="/opt/ngraph"):
    mkl_file = os.path.join(ng_path, "build/mkl/src/ext_mkl/include/mkl_version.h")
    additional_versions = ""
    if os.path.exists(mkl_file):
        mkl_version = read_or_fail(mkl_file)
        additional_versions += " / MKL: " + get_value(r".*INTEL_MKL_VERSION\s*(.*)", mkl_version)
    text = output_or_empty(["git", "describe", "--tags", "--abbrev=0"], cwd=ng_path) + additional_versions
    return text


@empty_string_if_failure
def plaidml_version(pl_path="/opt/plaidml/plaidml"):
    text = output_or_empty(["git", "rev-parse", "HEAD"], cwd=pl_path)
    text += " / " + subprocess.check_output(["/home/automation/anaconda3/bin/conda", "--version"]).strip().decode("utf-8")
    return text


@empty_string_if_failure
def aocl_version():
    return output_or_fail("/opt/altera/aocl-pro-rte/aclrte-linux64/bin/aocl version").split()[1]


@empty_string_if_failure
def gcc_version():
    return output_or_empty("gcc --version | head -n1")


@empty_string_if_failure
def cmake_version():
    return output_or_empty("cmake --version | head -n1")


@empty_string_if_failure
def dpkg_version(name):
    args = ["dpkg", "-s", name]
    text = subprocess.check_output(args).strip().decode("utf-8")
    return get_value(r"Version:\s*(.*)", text)


@empty_string_if_failure
def rpm_version(name):
    version = "%{VERSION}"
    command = "rpm -q --queryformat %s  $(rpm -qa | grep %s | head -n1)" % (version, name) %(version, name)
    args = shlex.split(command)
    return subprocess.check_output(args).strip().decode("utf-8")


@empty_string_if_failure
def onnx_python_version():
    return output_or_empty("python3 -c 'import onnx; print(onnx.__version__)'")


@empty_string_if_failure
def numpy_python_version():
    return output_or_empty("python3 -c 'import numpy; print(numpy.__version__)'")


@empty_string_if_failure
def onnx_runtime_version(onnx_rt_path="/opt/onnxruntime"):
    return output_or_empty(["git", "describe", "--tags", "--abbrev=0"], cwd=onnx_rt_path)


@empty_string_if_failure
def tf2onnx_version(tf_onnx_path="/opt/tf-onnx"):
    return output_or_empty(["git", "describe", "--tags", "--abbrev=0"], cwd=tf_onnx_path)


@empty_string_if_failure
def caffe2onnx_version(caffe_onnx_path="/opt/caffe-onnx"):
    return output_or_empty(["git", "describe", "--tags", "--abbrev=0"], cwd=caffe_onnx_path)

def software(model_zoo_path, job_name, openvino_path, omz_path):
    result = {
        "gcc":             gcc_version(),
        "cmake":           cmake_version(),
        "OpenVINO":        openvino_version(openvino_path),
        "OpenCV":          opencv_version(openvino_path),
        "MO":              mo_version(openvino_path),
        "InferenceEngine": ie_version(openvino_path),
        "Open Model Zoo":  open_model_zoo_version(omz_path),
        "Model Zoo":       model_zoo_version(model_zoo_path),
        "Tools":           model_zoo_check_version(model_zoo_path, "tools", True),
        "Public Models":   model_zoo_check_version(model_zoo_path, "models/public"),
        "Intel Models":    model_zoo_check_version(model_zoo_path, "models/intel"),
        "MXNet":           mxnet_version(),
        "Intel Caffe":     intel_caffe_version(),
        "CNTK":            cntk_version(),
        "TensorFlow":      tensorflow_version(),
        "TVM":             tvm_version(),
        "nGraph":          ngraph_version(),
        "PlaidML":         plaidml_version(),
        "FPGA Runtime":    aocl_version(),
        "Caffe2":          caffe2_version(),
        "NUMPY python":    numpy_python_version(),
        "ONNX python":     onnx_python_version(),
        "ONNX Runtime":    onnx_runtime_version(),
        "TF-to-ONNX":      tf2onnx_version(),
        "Caffe-to-ONNX":   caffe2onnx_version(),
        "nireq":           "N/A",
        "Intel(R) Deep Learning Streamer": dlstreamer_version()
    }
    if "Ubuntu" == distro.linux_distribution()[0]:
        result.update({
            "Boost":  dpkg_version("libboost-all-dev"),
            "Gflag":  dpkg_version("libgflags-dev"),
            "Glog":   dpkg_version("libgoogle-glog-dev"),
            "hdf5":   dpkg_version("libhdf5-dev"),
            "lmdb":   dpkg_version("liblmdb-dev")
        })
    elif ("yocto" in platform.release() or "centos" == platform.dist()[0]):
        result.update({
            "Boost":  rpm_version("boost-dev"),
            "Gflag":  rpm_version("gflags"),
            "Glog":   rpm_version("glog"),
            "hdf5":   rpm_version("hdf5"),
            "lmdb":   rpm_version("lmdb")
        })
    if "nvidia" in job_name:
        result.update({
            "Cuda":     dpkg_version("cuda"),
            "TensorRT": dpkg_version("tensorrt"),
        })
    return result


def gpu_frequency():
    fmax = read_or_empty("/sys/kernel/debug/dri/0/i915_max_freq") \
        or read_or_empty("/sys/class/drm/card0/gt_max_freq_mhz") \
        or 0
    fmin = read_or_empty("/sys/kernel/debug/dri/0/i915_min_freq") \
        or read_or_empty("/sys/class/drm/card0/gt_min_freq_mhz") \
        or 0
    return [int(fmin), int(fmax)]


def gpu_name():
    gpu_string = output_or_empty("glxinfo | grep 'Device'")
    if gpu_string:
        return gpu_string.split("Device: Mesa DRI ")[-1]
    gpu_string = output_or_empty("lspci | grep 'VGA compatible controller: '")
    if gpu_string:
        return gpu_string.split("VGA compatible controller: ")[-1]
    return ""


def gpu_info():
    minfreq, maxfreq = gpu_frequency()
    return {
        "Device name": gpu_name(),
        "SpeedMin (MHz)": minfreq,
        "SpeedMax (MHz)": maxfreq,
    }


def cpu_frequency():
    fmax = read_or_empty("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq") or 0
    fmin = read_or_empty("/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq") or 0
    # Hz to MHz
    fmax = int(float(fmax) / 1000)
    fmin = int(float(fmin) / 1000)
    return [int(fmin), int(fmax)]


def scaling_driver():
    return read_or_empty("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver")


def cpu_benchmark():
    try:
        script_location = os.path.dirname(os.path.realpath(__file__))
        time_benchmark = output_or_empty(os.path.join(script_location, "benchmark.sh"))
        return int(float(time_benchmark))
    except:
        return 0


@empty_string_if_failure
def cpu_product_link(product_name):
    if "amd" in product_name.lower():
        return ""
    search_words = []
    for substring in product_name.split():
        if "@" in substring:
            break
        if not ")" in substring and not "CPU" in substring and not "Processor" in substring:
            search_words.append(substring)
    if len(search_words) == 0:
        return ""
    search_string = "https://ark.intel.com/search?q="
    search_string += search_words[0]
    for i in range(1, len(search_words)):
        search_string += "+" + search_words[i]
    return " <a href=" + search_string + ">"+ product_name + "</a>"


def threads_per_core():
    if "yocto" in platform.release():
        return 0
    else:
        text_lscpu = output_or_empty("lscpu")
        return get_int_value(r"per core\s*:\s*(.*)", text_lscpu)


def hyperthreading(num_threads):
    if int(num_threads) < 2:
        return "OFF"
    else:
        return "ON"

def turbo_boost():
    try:
        is_turbo = read_or_fail("/sys/devices/system/cpu/cpufreq/boost")
        return "ON" if int(is_turbo) else "OFF"
    except:
        pass
    try:
        no_turbo = read_or_fail("/sys/devices/system/cpu/intel_pstate/no_turbo")
        return "OFF" if int(no_turbo) else "ON"
    except:
        pass
    return ""


def socket_count():
    try:
        file = read_or_fail("/proc/cpuinfo")
        return len(set(re.findall(r"^physical id\t: (.*)$", file, re.MULTILINE)))
    except:
        return "N/A"


def cpu_info():
    text = read_or_fail("/proc/cpuinfo")
    cpu_model = get_value(r"model name\s*:\s*(.*)", text)
    freq = cpu_frequency()
    num_threads = threads_per_core()
    result = {
        "Model":              cpu_model,
        "Product":            cpu_product_link(cpu_model),
        "SpeedMin (MHz)":     freq[0],
        "SpeedMax (MHz)":     freq[1],
        "ScalingDriver":      scaling_driver(),
        "NumberOfCPUs":       get_int_value(r"cpu cores\s*:\s*(.*)", text),
        "NumberOfSockets":    socket_count(),
        "Thread(s) per core": num_threads,
        "HT":                 hyperthreading(num_threads),
        "Turbo":              turbo_boost(),
        "Stepping":           get_value(r"stepping\s*:\s*(.*)", text),
        "LLC Cache":          get_int_value(r"cache size\s*:\s*(\d+)", text)
    }
    benchmark_result = cpu_benchmark()
    if benchmark_result:
        result["Benchmark"] = benchmark_result
    return result


@empty_string_if_failure
def opencl(cmd_prefix):
    text = output_or_empty(cmd_prefix + " clinfo")
    device_num = 0
    result = list()
    for block in text.split("Device Name"):
        if "Device Vendor" in block:
            block = "Device Name" + block
            result.append({
                "Device": device_num,
                "Name": get_value(r"Device Name\s*(.*)", block),
                "Vendor": get_value(r"Device Vendor\s*(.*)", block),
                "VendorID": get_value(r"Device Vendor ID\s*(.*)", block),
                "Version": get_value(r"Device Version\s*(.*)", block),
                "Driver": get_value(r"Driver Version\s*(.*)", block),
                "Type": get_value(r"Device Type\s*(.*)", block)
            })
            device_num += 1
    return result


def system_log():
    script_location = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(script_location, "systeminfo_helper.sh")
    text = output_or_empty(script_path)
    return text


def collect_configuration(args):
    context = {
        "hostname": hostname(),
        "motherboard": motherboard(),
        "cpu": cpu_info(),
        "gpu": gpu_info(),
        "memory": memory(),
        "bios": bios(),
        "os": os_release(),
        "software": software(args.modelzoo, args.job, args.openvino, args.open_model_zoo_repo),
        "opencl": opencl(args.prefix),
        "topologies": list_of_topologies(args.config, args.bitstreams, args.job, args.fp11),
        "system_log": system_log(),
        "JOB_BASE_NAME": args.job,
    }
    return context


def list_of_topologies(path_to_config, path_to_bitstreams, job_name, use_fp11):
    if not os.path.isfile(path_to_config):
        return []
    result = list()
    with open(path_to_config, "r") as infile:
        try:
            infile.readline()
            config = yaml.safe_load(infile)
        except:
            return []
    if path_to_bitstreams != "":
        fc = open(path_to_bitstreams, "r")
        fc.readline()
        bitstreams_config = yaml.safe_load(fc)
    for topology in config["topologies"]:
        name = topology["name"]
        frameworks = list()
        if "models" in topology.keys():
            for m in topology["models"]:
                frameworks.append(m["framework"])
        else:
            frameworks.append(topology["framework"])
        for framework in frameworks:
            try:
                if path_to_bitstreams != "":
                    for t2 in bitstreams_config["topologies"]:
                        if t2["name"] == name and t2["framework"] == framework:
                            if "fp11" in job_name or use_fp11:
                                name += "  /  " + t2["fp11_bitstream"]
                            else:
                                name += "  /  " + t2["fp16_bitstream"]
            except:
                pass
            result.append((name, framework))
    return result

def generate_json(context, dst_path):
    json_text = json.dumps(context, indent=1)
    f = open(dst_path, "w")
    f.write(json_text)
    f.close()


def main():
    parser = argparse.ArgumentParser(description="Display system info of linux machine.")
    parser.add_argument("-d",  "--dst",                        help="Output file with system configuration", required=True)
    parser.add_argument("-p",  "--prefix",     default="",     help="Prefix for specific commands (clinfo)")
    parser.add_argument("-c",  "--config",     default="",     help="Path to config")
    parser.add_argument("-b",  "--bitstreams", default="",     help="Path to bitstreams")
    parser.add_argument("-j",  "--job",        default="",     help="Job name")
    parser.add_argument("-m",  "--modelzoo",   default="",     help="Path to model-zoo code")
    parser.add_argument("--open-model-zoo-repo",   default="", help="Path to Open Model Zoo code repository")
    parser.add_argument("-js", "--json",       required=True,  help="JSON output file with system configuration")
    parser.add_argument("-f",  "--fp11",       default=False,  help="Use fp11", required=False)
    parser.add_argument("--openvino",                          help="OpenVINO(TM) toolkit path")
    args = parser.parse_args()

    if not args.openvino:
        args.openvino = os.environ.get("INTEL_OPENVINO_DIR", "/opt/intel/openvino")

    info = collect_configuration(args)

    generate_json(info, args.json)


if __name__ == "__main__":
    main()
