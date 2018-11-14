#include <iostream>
#include <fstream>

#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/ptrace.h>
#include <linux/perf_event.h>

using namespace std;

#include "rapl.h"
#include "event_list.h"


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
    RAPL rapl;
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
        rapl.sample();
        // ev.wait_event();
        // ev.reset();
    }
    ofstream save("hello.csv");
    ev.to_csv(save, {"instructions", "cache_ll", "branch_instructions", "branch_misses"});
    ofstream save2("hello_pw.csv");
    rapl.to_csv(save2);
}