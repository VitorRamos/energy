
#pragma once

#include <linux/perf_event.h>
#include <signal.h>

#include <iostream>
#include <vector>
#include <map>
class event_group
{
    enum sampling_method
    {
        time,
        interruption,
        wait
    };
    struct read_format
    {
        uint64_t nr;           /* The number of events */
        uint64_t time_enabled; /* if PERF_FORMAT_TOTAL_TIME_ENABLED */
        uint64_t time_running; /* if PERF_FORMAT_TOTAL_TIME_RUNNING */
        struct
        {
            uint64_t value; /* The value of the event */
            uint64_t id;    /* if PERF_FORMAT_ID */
        } values[];
    };
    std::vector<int> fds, ids;
    std::vector<std::vector<uint64_t>> samples;
    int pid, ncpu;
    sampling_method s_method= time;
    perf_event_mmap_page* mmap_data;
public:
    static std::map<int, event_group*> event_group_fd_instance;
public:
    event_group(int pid, sampling_method method= time);
    ~event_group();
    void add_event(int type_id, uint64_t config);
    void enable();
    void disable();
    void reset();
    void sample(bool reset=true);
    void delete_samples();
    void wait_event();
    static void interruption_event(int signum, siginfo_t* info, void* ucontext);
    std::ostream& to_csv(std::ostream& out, std::vector<std::string> columns);
};