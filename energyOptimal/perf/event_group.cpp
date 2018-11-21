
#include "event_group.h"

#include <asm/unistd.h>
#include <unistd.h>
#include <memory.h>
#include <poll.h>

#include <sys/mman.h>
#include <sys/sysinfo.h>
#include <sys/fcntl.h>
#include <sys/ioctl.h>

using namespace std;

event_group::event_group(int pid, sampling_method method)
{
    this->pid= pid;
    this->s_method= method;
    this->ncpu= get_nprocs();
}
event_group::~event_group()
{
    for(const auto& fd : fds)
        close(fd);
}
void event_group::add_event(int type_id, uint64_t config)
{
    int ret= 0, fd_id= 0;
    perf_event_attr pea;
    memset(&pea, 0, sizeof(perf_event_attr));
    pea.type = type_id;
    pea.size = sizeof(perf_event_attr);
    pea.config = config;
    pea.disabled = 1;
    pea.exclude_kernel = 1;
    pea.exclude_hv = 1;
    pea.inherit= 1;
    pea.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_ID | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;

    if(this->s_method == sampling_method::wait)
    {
        pea.sample_type= PERF_SAMPLE_IP;
        pea.sample_period= 1000;
        pea.wakeup_events= 1;
    }

    if(fds.size() == 0) // group leader
    {
        int fd= syscall(__NR_perf_event_open, &pea, pid, -1, -1, 0);
        #ifdef error_checking
        if(fd < 0)
            throw "Error creating group";
        #endif
        fds.push_back(fd);
        event_group_fd_instance[fd]= this;
    }
    else
    {
        int fd= syscall(__NR_perf_event_open, &pea, pid, -1, fds[0], 0);
        #ifdef error_checking
        if(fd < 0)
            throw "Error Joing the group";
        #endif
        fds.push_back(fd);
    }
    ret= ioctl(fds.back(), PERF_EVENT_IOC_ID, &fd_id);
    #ifdef error_checking
    if(ret < 0)
        throw "Error getting fd id";
    #endif
    ids.push_back(fd_id);

    if(this->s_method == sampling_method::interruption)
    {
        // Sampling with interruption
        struct sigaction sa;
        memset(&sa, 0, sizeof(struct sigaction));
        sa.sa_sigaction = interruption_event;
        sa.sa_flags = SA_SIGINFO;
        ret= sigaction(SIGIO, &sa, NULL);
        ret|= fcntl(fds.back(), F_SETFL, O_NONBLOCK|O_ASYNC);
        ret|= fcntl(fds.back(), F_SETSIG, SIGIO);
        ret|= fcntl(fds.back(), F_SETOWN, getpid());
        ret|= ioctl(fds.back(), PERF_EVENT_IOC_REFRESH, 1);
        #ifdef error_checking
        if(ret < 0)
            throw "Error setting up signal handler";
        #endif
    }

    if(this->s_method == sampling_method::wait)
    {
        //Sampling with mmap
        const int PAGE_SIZE= sysconf(_SC_PAGESIZE);
        const int DATA_SIZE= PAGE_SIZE;
        const int MMAP_SIZE= PAGE_SIZE+DATA_SIZE;
        mmap_data= (perf_event_mmap_page*)mmap(NULL, MMAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fds.back(), 0);
        #ifdef error_checking
        if(mmap_data == MAP_FAILED)
            throw "Error open memory map";
        #endif
    }
}
void event_group::enable()
{
    #ifdef error_checking
    if(fds.empty())
        throw "No events on group";
    #endif
    ioctl(fds[0], PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
}
void event_group::disable()
{
    #ifdef error_checking
    if(fds.empty())
        throw "No events on group";
    #endif
    ioctl(fds[0], PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
}
void event_group::reset()
{
    #ifdef error_checking
    if(fds.empty())
        throw "No events on group";
    #endif
    ioctl(fds[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
}
void event_group::sample(bool reset)
{
    void* buff= new uint8_t[sizeof(read_format)*fds.size()];
    size_t bytes_read= read(fds[0], buff, sizeof(read_format)*fds.size());
    #ifdef error_checking
    if(bytes_read != sizeof(read_format)*fds.size())
        throw "Error on sampling";
    #endif
    if(reset) ioctl(fds[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
    read_format *rf= (read_format*)buff;
    vector<uint64_t> row;
    row.push_back(rf->time_running);
    for(int i=0; i<rf->nr; i++)
        row.push_back(rf->values[i].value);
    samples.push_back(row);
}
void event_group::delete_samples()
{
    samples.clear();
}
void event_group::wait_event()
{
    #ifdef error_checking
    if(fds.empty())
        throw "No events on group";
    #endif
    // overflow test
    pollfd aux[1];
    aux[0].events= POLLIN;
    aux[0].fd= fds[0];
    poll(aux, 1, 500);
    for(int i=0; i<1; i++)
    {
        if(aux[i].revents & POLLIN)
        {
            cout << "Data ready" << endl;
            sample();
        }
        if(aux[i].revents & POLLHUP)
        {
            cout << "Hangup " << endl;
        }
    }
}
void event_group::interruption_event(int signum, siginfo_t* info, void* ucontext)
{
    if(info->si_code != POLL_HUP) {
        // Only POLL_HUP should happen.
        cerr << "Error interrupt" << endl;
        exit(EXIT_FAILURE);
    }
    cout << "Interruption" << endl;
    ioctl(info->si_fd, PERF_EVENT_IOC_REFRESH, 1);
    event_group_fd_instance[info->si_fd]->sample();
    // static map fd to class instance to call member function
}
ostream& event_group::to_csv(ostream& out, vector<string> columns)
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
