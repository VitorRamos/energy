
#pragma once

#include <linux/perf_event.h>
#include <signal.h>

#include <iostream>
#include <vector>
#include <map>

class event_single
{
    enum sampling_method
    {
        time,
        interruption,
        wait
    };
    std::vector<int> fds, ids;
    std::vector<uint64_t> samples;
    int pid, ncpu;
    sampling_method s_method= time;
    std::vector<perf_event_mmap_page*> mmap_data;
public:
    static std::map<int, event_single*> event_single_fd_instance;
public:
    event_single(sampling_method method= time);
    ~event_single();
    void add_event(int type_id, uint64_t config);
    void enable();
    void disable();
    void reset();
    void sample(bool reset=true);
    void delete_samples();
    void wait_event();
    static void interruption_event(int signum, siginfo_t* info, void* ucontext);
    std::ostream& to_csv(std::ostream& out, std::string columns);
};