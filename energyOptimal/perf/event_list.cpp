
#include "event_list.h"

#include <linux/perf_event.h>
#include <asm/unistd.h>
#include <sys/ioctl.h>
#include <sys/fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <memory.h>
#include <poll.h>

using namespace std;

event_list::event_list(int pid)
{
    this->pid= pid;
}
event_list::~event_list()
{
    for(const auto& fd : fds)
        close(fd);
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
    pea.inherit= 1;

    // pea.sample_type= PERF_SAMPLE_IP;
    // pea.sample_period= 1000;
    // pea.wakeup_events= 1;

    pea.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_ID | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
    if(fds.size() == 0) // group leader
        fds.push_back( syscall(__NR_perf_event_open, &pea, pid, -1, -1, 0) );
    else
        fds.push_back( syscall(__NR_perf_event_open, &pea, pid, -1, fds[0], 0) );

    // Sampling with interruption
    // struct sigaction sa;
    // memset(&sa, 0, sizeof(struct sigaction));
    // sa.sa_sigaction = perf_event_handler;
    // sa.sa_flags = SA_SIGINFO;
    // if (sigaction(SIGIO, &sa, NULL) < 0)
    //     cerr << "Error setting up signal handler\n";
    
    // fcntl(fds.back(), F_SETFL, O_NONBLOCK|O_ASYNC);
    // fcntl(fds.back(), F_SETSIG, SIGIO);
    // fcntl(fds.back(), F_SETOWN, getpid());
    // ioctl(fds.back(), PERF_EVENT_IOC_REFRESH, 1);

    // Sampling with mmap
    // perf_event_mmap_page* data;
    // const int PAGE_SIZE= sysconf(_SC_PAGESIZE);
    // const int DATA_SIZE= PAGE_SIZE;
    // const int MMAP_SIZE= PAGE_SIZE+DATA_SIZE;
    // data= (perf_event_mmap_page*)mmap(NULL, MMAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fds.back(), 0);
    // if(data == MAP_FAILED)
    //     cerr << "Error open memory map" << endl;

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
    vector<uint64_t> row;
    row.push_back(rf->time_running);
    for(int i=0; i<rf->nr; i++)
        row.push_back(rf->values[i].value);
    samples.push_back(row);
}
void event_list::perf_event_handler(int signum, siginfo_t* info, void* ucontext)
{
    if(info->si_code != POLL_HUP) {
        // Only POLL_HUP should happen.
        cerr << "Error interrupt" << endl;
        exit(EXIT_FAILURE);
    }
    cout << "Interruption" << endl;
    ioctl(info->si_fd, PERF_EVENT_IOC_REFRESH, 1);
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
void event_list::delete_samples()
{
    samples.clear();
}
void event_list::wait_event()
{
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