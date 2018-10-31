#include <iostream>

#include <cstdio>
#include <cstdlib>
#include <math.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>

#include <sys/wait.h>
#include <sys/syscall.h>
#include <sys/ptrace.h>
#include <sys/ioctl.h>
#include <linux/perf_event.h>
#include <linux/hw_breakpoint.h>
#include <asm/unistd.h>
#include <unistd.h>
#include <inttypes.h>

using namespace std;

// struct read_format
// {
//     uint64_t nr;
//     struct
//     {
//         uint64_t value;
//         uint64_t id;
//     } values[];
// };
struct read_format {
    uint64_t nr;            /* The number of events */
    uint64_t time_enabled;  /* if PERF_FORMAT_TOTAL_TIME_ENABLED */
    uint64_t time_running;  /* if PERF_FORMAT_TOTAL_TIME_RUNNING */
    struct {
        uint64_t value;     /* The value of the event */
        uint64_t id;        /* if PERF_FORMAT_ID */
    } values[];
};

int main(int argc, char** argv)
{
    pid_t pid= fork();
    if(pid == 0)
    {
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        int ret= execl(argv[1], (const char*)argv+1, NULL);
        if(ret < 0)
        {
            cerr << "ERROR ON EXECL" << endl;
        }
    }
    else if(pid > 0)
    {
        int pmcs[11]= {PERF_COUNT_HW_INSTRUCTIONS,
                    PERF_COUNT_HW_CPU_CYCLES,
                    PERF_COUNT_HW_CACHE_REFERENCES,
                    PERF_COUNT_HW_CACHE_MISSES,
                    PERF_COUNT_HW_BRANCH_INSTRUCTIONS,
                    PERF_COUNT_HW_BRANCH_MISSES,
                    PERF_COUNT_HW_BUS_CYCLES,
                    PERF_COUNT_HW_STALLED_CYCLES_FRONTEND,
                    PERF_COUNT_HW_STALLED_CYCLES_BACKEND,
                    PERF_COUNT_HW_REF_CPU_CYCLES};
        struct perf_event_attr pea;
        int fds[11];
        uint64_t ids[11];
        uint64_t vals[11];
        char buf[4096];
        struct read_format *rf = (struct read_format *)buf;
        int i;

        memset(&pea, 0, sizeof(struct perf_event_attr));
        pea.type = PERF_TYPE_HARDWARE;
        pea.size = sizeof(struct perf_event_attr);
        pea.config = pmcs[0];
        pea.disabled = 1;
        pea.exclude_kernel = 1;
        pea.exclude_hv = 1;
        pea.sample_type= PERF_SAMPLE_TIME;
        pea.sample_freq= 99;
        pea.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_ID | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
        fds[0] = syscall(__NR_perf_event_open, &pea, pid, -1, -1, 0);
        ioctl(fds[0], PERF_EVENT_IOC_ID, &ids[0]);

        for(int i=1; i<7; i++)
        {
            memset(&pea, 0, sizeof(struct perf_event_attr));
            pea.type = PERF_TYPE_HARDWARE;
            pea.size = sizeof(struct perf_event_attr);
            pea.config = pmcs[i];
            pea.disabled = 1;
            pea.exclude_kernel = 1;
            pea.exclude_hv = 1;
            pea.sample_type= PERF_SAMPLE_TIME;
            pea.sample_freq= 99;
            pea.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_ID | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING;
            fds[i] = syscall(__NR_perf_event_open, &pea, pid, -1, fds[0] /*!!!*/, 0);
            ioctl(fds[i], PERF_EVENT_IOC_ID, &ids[i]);
        }

        ioctl(fds[0], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
        ioctl(fds[0], PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
        while(1)
        {
            int status;
            waitpid(pid, &status, 0);
            if (WIFEXITED(status))
                break;

            ptrace(PTRACE_CONT, pid, 0, 0);
        }
        ioctl(fds[0], PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);
        read(fds[0], buf, sizeof(buf));
        cout << endl << "VALUES" << endl;
        for (i = 0; i < rf->nr; i++)
        {
            vals[i]= rf->values[i].value;
            cout << rf->values[i].id << " " 
                << rf->values[i].value << endl;
        }
    }
}