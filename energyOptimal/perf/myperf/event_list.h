
#pragma once

#include <iostream>
#include <vector>

class event_list
{
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
    std::vector<std::vector<int>> samples;
    int pid;
public:
    event_list(int pid);
    void add_event(int type_id, uint64_t config);
    void enable();
    void disable();
    void reset();
    void sample();
    std::ostream& to_csv(std::ostream& out, std::vector<std::string> columns);
    void wait_event();
};