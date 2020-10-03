#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <chrono>
#include <thread>

#include <iostream>
#include <fstream>
#include <getopt.h>
#include <signal.h>

extern "C" {
#include "sm.h"
}

volatile sig_atomic_t endf = 0;
void ctrlc_handler(int s)
{
	printf("CTRL-C handled\n");
	endf = 1;
}

struct SysMonStat sm = {};

const unsigned int ONE_SECOND = 1000U;

std::string interval_stats_str;
std::string interval_stats_json_str;
std::string header;
std::ofstream csvfile;

// csv header
// start-time,
// cpu-core-0,cpu-core-1,cpu-core-2,cpu-core-3,cpu-core-4,cpu-core-5,cpu-core-6,cpu-core-7,
// cpu-freq-0-MHz,cpu-freq-1-MHz,cpu-freq-2-MHz,cpu-freq-3-MHz,cpu-freq-4-MHz,cpu-freq-5-MHz,cpu-freq-6-MHz,cpu-freq-7-MHz,
// gpu-freq,gpu-freq-act,gpu-rc6,gpu-irq,gpu-imc-reads,gpu-imc-writes,
// gpu-Render/3D-0-busy,gpu-Render/3D-0-sema,gpu-Render/3D-0-wait,
// gpu-Blitter-0-busy,gpu-Blitter-0-sema,gpu-Blitter-0-wait,
// gpu-Video-0-busy,gpu-Video-0-sema,gpu-Video-0-wait,
// gpu-Video-1-busy,gpu-Video-1-sema,gpu-Video-1-wait,
// gpu-VideoEnhance-0-busy,gpu-VideoEnhance-0-sema,gpu-VideoEnhance-0-wait,
// minflt,majflt,voluntary_ctxt_switches,nonvoluntary_ctxt_switches,threads,
// resident_set_size,
// stop-time,
//

void string_formatter(const std::string &name, const std::string &value)
{
	header += (name + ",");
	interval_stats_str += (value + ",");
	interval_stats_json_str += (name + ":" + value + "\n");
}

void report_data_val(const std::string &name, double value)
{
	string_formatter(name, std::to_string(value));
}

void report_data_val(const std::string &name, unsigned long value)
{
	string_formatter(name, std::to_string(value));
}

void print_stats(bool start_interval)
{ 
    static bool print_header = true;

	if (start_interval == false) {
		interval_stats_str = "";
		interval_stats_json_str = "";
		header = "";
	} else {
		//insert a newline for the csv formatter
		interval_stats_str += "\n";
		//header += "\n";
		//printf("%s\n", header.data());
		//printf("%s\n", interval_stats_str.data());
		if (print_header) 
        {
            csvfile << header << std::endl;
			print_header = false;
        }
        csvfile << interval_stats_str;
		
		//json string print
		printf("{\n%s}\n", interval_stats_json_str.data());
	}
}


static void send_stat()
{
	float *cpu_load;
	int cpu_id;
	int cpu_num;
	int block_id;
	float avg_cpu_load;
	float avg_cpu_frequency;

	cpu_load = &sm.cpu.cpu_load[0];
	cpu_num = sm.cpu.cpu_num;

	ProcStatReaderErrors error_code = sys_mon_compute(&sm);

	if (error_code != SUCCESS) {
		printf("ProcStat: %s\n", gst_ru_proc_stat_error_message(error_code));
	}

	print_stats(false);

	report_data_val("start-time", sm.timestamp_s);

    float total = 0;
	for (cpu_id = 0; cpu_id < cpu_num; ++cpu_id) {
		char name[32];
		sprintf(name, "cpu-core-%d", cpu_id);
		report_data_val(name, cpu_load[cpu_id]);
		total += cpu_load[cpu_id];
	}
	avg_cpu_load = total / cpu_num;
	report_data_val("cpu-cores-avg", avg_cpu_load);

    total = 0;
	if (sm.cpu.cpu_frequency_available) {
		for (cpu_id = 0; cpu_id < cpu_num; cpu_id++) {
			char name[32];
			sprintf(name, "cpu-freq-%d-MHz", cpu_id);
			report_data_val(name, sm.cpu.cpu_frequency[cpu_id]);
			total += sm.cpu.cpu_frequency[cpu_id];
		}
	}
	avg_cpu_frequency = total / cpu_num;
	report_data_val("cpu-freq-avg-MHz", avg_cpu_frequency);

	//for (int i = 0; i < sm.cpu.pwr_stat_ref.power_consumption_array_length; i++)
	//{
	//    report_data_val(sm.cpu.pwr_stat_ref.power_consumption_array[i].name, sm.cpu.pwr_stat_ref.power_consumption_array[i].value);
	//}

    report_data_val("cpu-memory-total-kB", sm.cpu.mem_total);
	report_data_val("cpu-memory-used-kB", sm.cpu.mem_used);
    report_data_val("cpu-memory-free-kB", sm.cpu.mem_free);

	report_data_val("gpu-freq", sm.gpu.freq_req);
	report_data_val("gpu-freq-act", sm.gpu.freq_act);
	report_data_val("gpu-rc6", sm.gpu.rc6);
	report_data_val("gpu-irq", sm.gpu.irq);
	report_data_val("gpu-imc-reads", sm.gpu.imc_reads);
	report_data_val("gpu-imc-writes", sm.gpu.imc_writes);
	for (block_id = 0; block_id < 5; ++block_id) {
		char tmp[32];
		char tmp1[32];
		char tmp2[32];
		if (sm.gpu.blocks[block_id].dispName) {
			sprintf(tmp, "gpu-%s-busy", sm.gpu.blocks[block_id].dispName);
			sprintf(tmp1, "gpu-%s-sema", sm.gpu.blocks[block_id].dispName);
			sprintf(tmp2, "gpu-%s-wait", sm.gpu.blocks[block_id].dispName);
			report_data_val(tmp, sm.gpu.blocks[block_id].busy);
			report_data_val(tmp1, sm.gpu.blocks[block_id].sema);
			report_data_val(tmp2, sm.gpu.blocks[block_id].wait);
		}
	}    

	if (sm.pid != -1) {
		report_data_val("minflt", static_cast<float>(sm.proc.minflt));
		report_data_val("majflt", static_cast<float>(sm.proc.majflt));
		report_data_val("voluntary_ctxt_switches", static_cast<float>(sm.proc.voluntary_ctxt_switches));
		report_data_val("nonvoluntary_ctxt_switches", static_cast<float>(sm.proc.nonvoluntary_ctxt_switches));
		report_data_val("threads", static_cast<float>(sm.proc.threads));
		report_data_val("resident_set_size", sm.proc.resident_set_size);
	}

	report_data_val("stop-time", sm.timestamp_e);

	print_stats(true);
}

void parse_arguments(int argc, char *argv[], int *pid, unsigned int *interval, std::string& fname)
{
	try 
    {	
	    std::string pid_name = "pid";
	    std::string interval_name = "interval";
	    std::string filename = "output";
	    std::string short_names = "p:P:i:I:o:O:";
	    option long_options[] = { { pid_name.c_str(), required_argument, nullptr, 'p' },
				                  { interval_name.c_str(), required_argument, nullptr, 'i' },
				                  { filename.c_str(), required_argument, nullptr, 'o' },
				                  { nullptr, 0, nullptr, 0 } 
                                };

	    while (true) {
		    int option_index = -1;
		    int ret_value = getopt_long(argc, argv, short_names.c_str(), long_options, &option_index);
		    switch (ret_value) {
		    case -1:
			    return;
		    case 0:
			    if (pid_name.compare(long_options[option_index].name))
				    *pid = std::stoi(optarg);
			    else if (interval_name.compare(long_options[option_index].name))
				    *interval = std::stoul(optarg);
			    else if (filename.compare(long_options[option_index].name))
				    fname = std::string(optarg);
			    break;
		    case 'p':
		    case 'P':
			    *pid = std::stoi(optarg);
			    break;
		    case 'i':
		    case 'I':
			    std::cout << optarg << std::endl;
			    *interval = std::stoul(optarg);
			    break;
		    case 'o':
		    case 'O':
			    std::cout << optarg << std::endl;			    
			    fname = std::string(optarg);
			    break;
		    case '?':
			    throw std::invalid_argument("Unexpected argument");
		    default:
			    throw std::invalid_argument("Unexpected arguments parse result");
		    }
	    }
    }

    catch (std::exception &e) {
		std::cout << e.what() << std::endl;
    }
}

int main(int argc, char *argv[])
{
	unsigned int interval = ONE_SECOND;
	int pid = -1;
	std::string out_fname("collector-out.csv");
	struct sigaction ctrlc_action;

	try {
		std::cout.flush();
		parse_arguments(argc, argv, &pid, &interval, out_fname);
		printf( "printing entered filename: %s", out_fname.data()) ;
		csvfile.open(out_fname.data(), std::fstream::out | std::fstream::trunc);
	} catch (const std::exception &e) {
		std::cout << e.what() << std::endl;
		return EXIT_FAILURE;
	}
	    
    if (pid == -1)
    {
        std::cout << "Missing pid parameter, process stats will not be collected" << std::endl;
        //return EXIT_FAILURE;
    }
    
	/*Init ctrl-c handler and action*/
	ctrlc_action.sa_handler = ctrlc_handler;
	sigemptyset(&ctrlc_action.sa_mask);
	ctrlc_action.sa_flags = 0;
	sigaction(SIGINT, &ctrlc_action, NULL);

	sys_mon_init(&sm);
	sys_mon_setpid(&sm, pid);
	std::cout << "collector started" << std::endl;
	for (;;) {
		send_stat();
		std::this_thread::sleep_for(std::chrono::milliseconds(interval));
		if (0 != endf)
			break;
	}

	printf("collector is stopping\n");
	csvfile.close();
    sys_mon_finalize(&sm);
}
