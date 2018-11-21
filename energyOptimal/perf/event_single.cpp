#include "event_single.h"

#include <asm/unistd.h>
#include <unistd.h>
#include <memory.h>
#include <poll.h>

#include <sys/mman.h>
#include <sys/sysinfo.h>
#include <sys/fcntl.h>
#include <sys/ioctl.h>

using namespace std;

#define error_checking

event_single::event_single(sampling_method method)
{
    this->s_method= method;
    this->ncpu= get_nprocs();
}
event_single::~event_single()
{
    for(const auto& fd : fds)
        close(fd);
}
void event_single::add_event(int type_id, uint64_t config)
{
    int ret= 0, fd_id= 0;
    perf_event_attr pea;
    memset(&pea, 0, sizeof(perf_event_attr));
    pea.type = type_id;
    pea.size = sizeof(perf_event_attr);
    pea.config = config;

    if(this->s_method == sampling_method::wait)
    {
        pea.sample_type= PERF_SAMPLE_IP;
        pea.sample_period= 1000;
        pea.wakeup_events= 1;
    }

    for(int i=0; i<this->ncpu; i++)
    {
        int fd= syscall(__NR_perf_event_open, &pea, -1, i, -1, 0);
        #ifdef error_checking
        if(fd < 0)
            throw "Error creating event";
        #endif
        fds.push_back(fd);
        event_single_fd_instance[fd]= this;

        ret= ioctl(fds.back(), PERF_EVENT_IOC_ID, &fd_id);
        #ifdef error_checking
        if(ret < 0)
            throw "Error getting fd id";
        #endif
        ids.push_back(fd_id);
    }

    if(this->s_method == sampling_method::interruption)
    {
        // Sampling with interruption
        struct sigaction sa;
        memset(&sa, 0, sizeof(struct sigaction));
        sa.sa_sigaction = interruption_event;
        sa.sa_flags = SA_SIGINFO;
        ret= sigaction(SIGIO, &sa, NULL);
        for(const auto& fd: fds)
        {
            ret|= fcntl(fd, F_SETFL, O_NONBLOCK|O_ASYNC);
            ret|= fcntl(fd, F_SETSIG, SIGIO);
            ret|= fcntl(fd, F_SETOWN, getpid());
            ret|= ioctl(fd, PERF_EVENT_IOC_REFRESH, 1);
            #ifdef error_checking
            if(ret < 0)
                throw "Error setting up signal handler";
            #endif
        }
    }

    if(this->s_method == sampling_method::wait)
    {
        //Sampling with mmap
        const int PAGE_SIZE= sysconf(_SC_PAGESIZE);
        const int DATA_SIZE= PAGE_SIZE;
        const int MMAP_SIZE= PAGE_SIZE+DATA_SIZE;
        for(const auto& fd: fds)
        {
            perf_event_mmap_page* mmap_data_= (perf_event_mmap_page*)mmap(NULL, MMAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
            #ifdef error_checking
            if(mmap_data_ == MAP_FAILED)
                throw "Error open memory map";
            #endif
            this->mmap_data.push_back(mmap_data_);
        }
    }
}
void event_single::enable()
{
    #ifdef error_checking
    if(fds.empty())
        throw "No events on group";
    #endif
    for(const auto& fd: fds)
        ioctl(fd, PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
}
void event_single::disable()
{
    #ifdef error_checking
    if(fds.empty())
        throw "No events on group";
    #endif
    for(const auto& fd: fds)
        ioctl(fd, PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
}
void event_single::reset()
{
    #ifdef error_checking
    if(fds.empty())
        throw "No events on group";
    #endif
    for(const auto& fd: fds)
        ioctl(fd, PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
}
void event_single::sample(bool reset)
{
    int64_t c_val= 0;
    for(int i=0; i<fds.size(); i++)
    {
        int64_t aux;
        read(fds[i], &aux, sizeof(int64_t));
        c_val+=aux;
    }
    if(reset) this->reset();
    samples.push_back(c_val);
}
void event_single::delete_samples()
{
    samples.clear();
}
void event_single::wait_event()
{
    #ifdef error_checking
    if(fds.empty())
        throw "No events on group";
    #endif
    // overflow test
    pollfd aux[fds.size()];
    for(int i=0; i<fds.size(); i++)
    {
        aux[i].events= POLLIN;
        aux[i].fd= fds[i];
    }
    poll(aux, fds.size(), 500);
    for(int i=0; i<fds.size(); i++)
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
void event_single::interruption_event(int signum, siginfo_t* info, void* ucontext)
{
    if(info->si_code != POLL_HUP) {
        // Only POLL_HUP should happen.
        cerr << "Error interrupt" << endl;
        exit(EXIT_FAILURE);
    }
    cout << "Interruption" << endl;
    ioctl(info->si_fd, PERF_EVENT_IOC_REFRESH, 1);
    // static map fd to class instance to call member function
    event_single_fd_instance[info->si_fd]->sample();
}
ostream& event_single::to_csv(ostream& out, string column)
{
    out << column << endl;
    for(const auto& s : samples)
        out << s << endl;
    return out;
}
