#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <chrono>
#include <thread>
#include "zmq.hpp"

#include <iostream>
#include <getopt.h>
#include <signal.h>

extern "C"
{
#include "sm.h"
}

volatile sig_atomic_t endf = 0;
void ctrlc_handler(int s)
{
    printf("CTRL-C handled\n");
    endf = 1;
}

#define ZMQ_ADDRESS "tcp://127.0.0.1:5560"

struct SysMonStat sm = {};

const unsigned int ONE_SECOND = 1000U;
static bool connected = false;
static zmq::context_t context(1);
static zmq::socket_t publisher(context, ZMQ_PUB);

bool zmq_send(const std::string &name, double value)
{
    if (!connected)
    {
        printf("Binding ZMQ address %s\n", ZMQ_ADDRESS);
        publisher.bind(ZMQ_ADDRESS);
        connected = true;
    }
    std::string str = name + ":" + std::to_string(value);
    //printf("%s\n", str.data());
    zmq::message_t message(str.size());
    memcpy(message.data(), str.data(), str.size());
    return publisher.send(message, ZMQ_NOBLOCK);
}

bool zmq_send(const std::string &name, unsigned long value)
{
    if (!connected)
    {
        printf("Binding ZMQ address %s\n", ZMQ_ADDRESS);
        publisher.bind(ZMQ_ADDRESS);
        connected = true;
    }
    std::string str = name + ":" + std::to_string(value);
    //printf("%s\n", str.data());
    zmq::message_t message(str.size());
    memcpy(message.data(), str.data(), str.size());
    return publisher.send(message, ZMQ_NOBLOCK);
}

static void send_stat()
{
    float *cpu_load;
    int cpu_id;
    int cpu_num;
    int block_id;

    cpu_load = &sm.cpu.cpu_load[0];
    cpu_num = sm.cpu.cpu_num;

    ProcStatReaderErrors error_code = sys_mon_compute(&sm);

    if (error_code != SUCCESS)
    {
        printf("ProcStat: %s\n", gst_ru_proc_stat_error_message(error_code));
    }

    zmq_send("start-time", sm.timestamp_s);

    for (cpu_id = 0; cpu_id < cpu_num; ++cpu_id)
    {
        char name[32];
        sprintf(name, "cpu-core-%d", cpu_id);
        zmq_send(name, cpu_load[cpu_id]);
    }

    if (sm.cpu.cpu_frequency_available)
    {
        for (cpu_id = 0; cpu_id < cpu_num; cpu_id++)
        {
            char name[32];
            sprintf(name, "cpu-freq-%d-MHz", cpu_id);
            zmq_send(name, sm.cpu.cpu_frequency[cpu_id]);
        }
    }

    for (int i = 0; i < sm.cpu.pwr_stat_ref.power_consumption_array_length; i++)
    {
        zmq_send(sm.cpu.pwr_stat_ref.power_consumption_array[i].name, sm.cpu.pwr_stat_ref.power_consumption_array[i].value);
    }

    zmq_send("gpu-freq", sm.gpu.freq_req);
    zmq_send("gpu-freq-act", sm.gpu.freq_act);
    zmq_send("gpu-rc6", sm.gpu.rc6);
    zmq_send("gpu-irq", sm.gpu.irq);
    zmq_send("gpu-imc-reads", sm.gpu.imc_reads);
    zmq_send("gpu-imc-writes", sm.gpu.imc_writes);
    for (block_id = 0; block_id < 5; ++block_id)
    {
        char tmp[32];
        char tmp1[32];
        char tmp2[32];
        if (sm.gpu.blocks[block_id].dispName)
        {
            sprintf(tmp, "gpu-%s-busy", sm.gpu.blocks[block_id].dispName);
            sprintf(tmp1, "gpu-%s-sema", sm.gpu.blocks[block_id].dispName);
            sprintf(tmp2, "gpu-%s-wait", sm.gpu.blocks[block_id].dispName);
            zmq_send(tmp, sm.gpu.blocks[block_id].busy);
            zmq_send(tmp1, sm.gpu.blocks[block_id].sema);
            zmq_send(tmp2, sm.gpu.blocks[block_id].wait);
        }
    }

    zmq_send("minflt", static_cast<float>(sm.proc.minflt));
    zmq_send("majflt", static_cast<float>(sm.proc.majflt));
    zmq_send("voluntary_ctxt_switches", static_cast<float>(sm.proc.voluntary_ctxt_switches));
    zmq_send("nonvoluntary_ctxt_switches", static_cast<float>(sm.proc.nonvoluntary_ctxt_switches));
    zmq_send("threads", static_cast<float>(sm.proc.threads));
    zmq_send("resident_set_size", sm.proc.resident_set_size);

    zmq_send("stop-time", sm.timestamp_e);
}

void parse_arguments(int argc, char *argv[], int *pid, unsigned int *interval)
{
    std::string pid_name = "pid";
    std::string interval_name = "interval";
    std::string short_names = "p:i:";
    option long_options[] =
        {
            {pid_name.c_str(), required_argument, nullptr, 'p'},
            {interval_name.c_str(), required_argument, nullptr, 'i'},
            {nullptr, 0, nullptr, 0}};

    while (true)
    {
        int option_index = -1;
        int ret_value = getopt_long(argc, argv, short_names.c_str(), long_options, &option_index);
        switch (ret_value)
        {
        case -1:
            return;
        case 0:
            if (pid_name.compare(long_options[option_index].name))
                *pid = std::stoi(optarg);
            else if (interval_name.compare(long_options[option_index].name))
                *interval = std::stoul(optarg);
            break;
        case 'p':
            *pid = std::stoi(optarg);
            break;
        case 'i':
            std::cout << optarg << std::endl;
            *interval = std::stoul(optarg);
            break;
        case '?':
            throw std::invalid_argument("Unexpected argument");
        default:
            throw std::invalid_argument("Unexpected arguments parse result");
        }
    }
}

int main(int argc, char *argv[])
{
    unsigned int interval = ONE_SECOND;
    int pid = -1;
    struct sigaction ctrlc_action;

    try
    {
        parse_arguments(argc, argv, &pid, &interval);
    }
    catch (const std::exception &e)
    {
        std::cout << e.what() << std::endl;
        return EXIT_FAILURE;
    }
    if (pid == -1)
    {
        std::cout << "Missing pid parameter" << std::endl;
        return EXIT_FAILURE;
    }

    /*Init ctrl-c handler and action*/
    ctrlc_action.sa_handler = ctrlc_handler;
    sigemptyset(&ctrlc_action.sa_mask);
    ctrlc_action.sa_flags = 0;
    sigaction(SIGINT, &ctrlc_action, NULL);


    sys_mon_init(&sm);
    sys_mon_setpid(&sm, pid);
    std::cout << "Service started" << std::endl;
    for (;;)
    {
        send_stat();
        std::this_thread::sleep_for(std::chrono::milliseconds(interval));
        if(0 != endf) break;
    }
    
    printf("Service is stopping\n");
    sys_mon_finalize(&sm);
}
