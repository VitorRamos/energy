#include <iostream>
#include <fstream>

#include <map>
#include <tuple>

#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/ptrace.h>
#include <linux/perf_event.h>

using namespace std;

#include "event_single.h"
#include "event_group.h"
#include "list_events.h"
#include "rapl.h"

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

std::map<int, event_single*> event_single::event_single_fd_instance;
std::map<int, event_group*> event_group::event_group_fd_instance;

class profiler
{
    list_events evs_list;
    vector<event_single> single_evs;
    vector<string> single_evs_names;
    vector<event_group> group_evs;
    vector<string> group_evs_names;
private:

public:
    void get_all_single_events()
    {
        for(const auto& e: evs_list.get_evs())
        {  
            string str_event= e.second;
            int type= get<0>(e.first);
            int config= get<1>(e.first);
            while(str_event.find(':') != string::npos)
                str_event.replace(str_event.find(':'),1,"_");
            while(str_event.find('-') != string::npos)
                str_event.replace(str_event.find('-'),1,"_");
            if(type > 4)
            {
                single_evs.emplace_back(type, config);
                single_evs.emplace_back(type, config);
            }
        }
    }
    void get_all_5group_events()
    {
        for(const auto& e: evs_list.get_evs())
        {  
            string str_event= e.second;
            int type= get<0>(e.first);
            int config= get<1>(e.first);
            while(str_event.find(':') != string::npos)
                str_event.replace(str_event.find(':'),1,"_");
            while(str_event.find('-') != string::npos)
                str_event.replace(str_event.find('-'),1,"_");
            if(type != 1 && type < 4)
            {
                group_evs.emplace_back(type, config);
                single_evs.emplace_back(type, config);
            }
        }
    }
    profiler()
    {
        evs_list.supported_pmus();
    }
};

int main(int argc, char** argv)
{
    profiler perf;
    
    //e.generate_header();
    
    // ev.reset();
    // ev.enable();
    // while(1)
    // {
    //     ev.sample();
    //     ev.to_csv(cout, cols);
    //     usleep(1e5);
    // }
    //e.generate_header();

    // vector<vector<string>> args;
    // ifstream files("benchmarks/polybench/files.txt");
    // string names;
    // while(files >> names)
    // {
    //     args.push_back( {"benchmarks/polybench/"+names} );
    // }
    // int cnt=0;
    // for(const auto& arg: args)
    // {
    //     argv= convert(arg);
    //     string pname= get_pname(argv[0]);
    //     ofstream save;
    //     ostream* output= &save;
    //     cout << "Executing " << pname << endl;
    //     int pid = create_wrokload(argv);
    //     RAPL rapl;
    //     event_list ev(pid);
        // ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS);
    //     ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_LL);
    //     ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_INSTRUCTIONS);
    //     ev.add_event(PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES);
    //     ev.add_event(DTLB_STORES_TYPE, DTLB_STORES_CONFIG);
    //     ev.reset();
    //     ev.enable();
    //     int status;
    //     waitpid(pid, &status, 0);
    //     ptrace(PTRACE_CONT, pid, 0, 0);
    //     while(1)
    //     {
    //         waitpid(pid, &status, WNOHANG);
    //         if (WIFEXITED(status))
    //             break;
    //         usleep(1e5);
    //         ev.sample(false);
    //         rapl.sample(false);
    //     }
    //     save.open("data/"+pname+".csv");
    //     ev.to_csv(*output, {"instructions", "cache_ll", "branch_instructions", "branch_misses"});
    //     save.close();
    //     save.open("data/"+pname+"_pw"+".csv");
    //     rapl.to_csv(*output);
    //     cnt++;
    // }
}