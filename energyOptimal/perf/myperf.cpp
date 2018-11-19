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
        int fd= open("out.stdout",  O_WRONLY | O_CREAT, S_IRUSR | S_IWUSR);
        dup2(fd, STDOUT_FILENO);
        fd= open("out.stderr",  O_WRONLY | O_CREAT, S_IRUSR | S_IWUSR);
        dup2(fd, STDERR_FILENO);
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        if( execl(argv[0], (const char *)argv, NULL) < 0)
        {
            cerr << "Error on executing worload" << endl;
        }
    }
    return pid;
}

string get_pname(string x)
{
    size_t bs= x.find_last_of('/');
    if(bs == string::npos)
        return x;
    return x.substr(bs+1);
    
}

char** convert(const vector<string>& v)
{
    char** args= new char*[v.size()+1];
    for(unsigned int i=0; i<v.size(); i++)
        args[i]= const_cast<char*>(v[i].c_str());
    args[v.size()]= nullptr;
    return args;
}


int main(int argc, char** argv)
{
    vector<vector<string>> args= {{"benchmarks/hello"}, {"benchmarks/hello"}};
    vector<vector<string>> args;
    ifstream files("benchmarks/polybench/files.txt");
    string names;
    while(files >> names)
    {
        args.push_back( {"benchmarks/polybench/"+names} );
    }

    int cnt=0;
    for(const auto& arg: args)
    {
        argv= convert(arg);
        string pname= get_pname(argv[0]);
        ofstream save;
        ostream* output= &save;
        cout << "Executing " << pname << endl;

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
        save.open("data/"+pname+".csv");
        ev.to_csv(*output, {"instructions", "cache_ll", "branch_instructions", "branch_misses"});
        save.close();
        save.open("data/"+pname+"_pw"+".csv");
        rapl.to_csv(*output);
        cnt++;
    }

    // pid_t pid = create_wrokload(argv+1);
    // RAPL rapl;
    // event_list ev(pid);
    // ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS);
    // ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_LL);
    // ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_INSTRUCTIONS);
    // ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES);
    // ev.reset();
    // ev.enable();
    // int status;
    // waitpid(pid, &status, 0);
    // ptrace(PTRACE_CONT, pid, 0, 0);
    // while(1)
    // {
    //     waitpid(pid, &status, WNOHANG);
    //     if (WIFEXITED(status))
    //         break;
    //     usleep(1e4);
    //     // ev.wait_event();
    //     // ev.reset();
    // }
    // ev.sample();
    // rapl.sample();
    // ev.to_csv(cout, {"instructions", "cache_ll", "branch_instructions", "branch_misses"});
    // rapl.to_csv(cout);
}