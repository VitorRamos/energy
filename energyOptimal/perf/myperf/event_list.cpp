
#include "event_list.h"

#include <linux/perf_event.h>
#include <asm/unistd.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <memory.h>
#include <poll.h>

using namespace std;

event_list::event_list(int pid)
{
    this->pid= pid;
}
void event_list::add_event(int type_id, uint64_t config)
{
    perf_event_attr pea;
    int aux;
    memset(&pea, 0, sizeof(perf_event_attr));
    pea.type = type_id;
    pea.size = sizeof(perf_event_attr);
    pea.config = config;
    pea.disabled = 1;
    pea.exclude_kernel = 1;
    pea.exclude_hv = 1;

    // overflow test
    // pea.sample_period= 1; 
    // pea.sample_type= PERF_SAMPLE_IP;
    // pea.wakeup_events= 1;
    
    pea.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_ID | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
    if(fds.size() == 0) // group leader
        fds.push_back( syscall(__NR_perf_event_open, &pea, pid, -1, -1, 0) );
    else
        fds.push_back( syscall(__NR_perf_event_open, &pea, pid, -1, fds[0], 0) );

    ioctl(fds.back(), PERF_EVENT_IOC_ID, &aux);
    ids.push_back(aux);
}
void event_list::enable()
{
    ioctl(fds[0], PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
}
void event_list::disable()
{
    ioctl(fds[0], PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
}
void event_list::reset()
{
    ioctl(fds[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
}
void event_list::sample()
{
    void* buff= new uint8_t[4096];
    read(fds[0], buff, 4096);
    ioctl(fds[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
    read_format *rf= (read_format*)buff;
    vector<int> row;
    row.push_back(rf->time_running);
    for(int i=0; i<rf->nr; i++)
        row.push_back(rf->values[i].value);
    samples.push_back(row);
}
ostream& event_list::to_csv(ostream& out, vector<string> columns)
{
    out << "time,";
    if(columns.size()+1 == ids.size())
    {
        for(const auto& i : ids)
        {
            out << i;
            if(&i != &ids.back())
                out << ",";
        }
    }
    else
    {
        for(const auto& i : columns)
        {
            out << i;
            if(&i != &columns.back())
                out << ",";
        }
    }
    out << endl;
    for(const auto& s : samples)
    {
        for(const auto& p: s)
        {
            out << p;
            if(&p != &s.back())
                out << ",";
        }
        out << endl;
    }
    return out;
}
void event_list::wait_event()
{
    // overflow test
    pollfd aux[1];
    aux[0].fd= fds[0];
    // aux[0].events= POLLIN;
    poll(aux, 1, 500);
    for(int i=0; i<1; i++)
    {
        if(aux[i].revents & POLLIN)
        {
            cout << "Data ready" << endl;
        }
        if(aux[i].revents & POLLHUP)
        {
            // cout << "Hangup " << endl;
        }
    }
}