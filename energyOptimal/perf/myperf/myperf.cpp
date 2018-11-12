#include <iostream>
#include <fstream>
#include <vector>

#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ptrace.h>
#include <asm/unistd.h>
#include <signal.h>
#include <poll.h>
#include <sys/wait.h>
#include <unistd.h>
#include <memory.h>
#include <fcntl.h>

using namespace std;

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
    vector<int> fds, ids;
    vector<vector<int>> samples;
    int pid;
public:
    event_list(int pid)
    {
        this->pid= pid;
    }
    void add_event(perf_type_id type_id, uint64_t config)
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
    void enable()
    {
        ioctl(fds[0], PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
    }
    void disable()
    {
        ioctl(fds[0], PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
    }
    void reset()
    {
        ioctl(fds[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
    }
    void sample()
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
    ostream& to_csv(ostream& out, vector<string> columns)
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
    void wait_event()
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
};

pid_t create_wrokload(char** argv)
{
    pid_t pid= fork();
    if(pid == 0)
    {
        int fd= open("output",  O_WRONLY | O_CREAT, S_IRUSR | S_IWUSR);
        dup2(fd, STDOUT_FILENO);
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        if( execl(argv[1], (const char *)argv+1, NULL) < 0)
        {
            cerr << "Error on executing worload" << endl;
        }
    }
    return pid;
}

int main(int argc, char** argv)
{
    int pid = create_wrokload(argv);
    event_list ev(pid);
    ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS);
    ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_LL);
    ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_INSTRUCTIONS);
    ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES);
    ev.reset();
    ev.enable();
    int status;
    waitpid(pid, &status, 0);
    ptrace(PTRACE_CONT, pid, 0, 0);
    while(1)
    {
        waitpid(pid, &status, WNOHANG);
        if (WIFEXITED(status))
                break;
        usleep(1e4);
        ev.sample();
        // ev.reset();
    }
    ofstream save("hello.csv");
    ev.to_csv(save, {"instructions", "cache_ll", "branch_instructions", "branch_misses"});
}