#include <iostream>
#include <vector>
#include <map>

#include <sys/stat.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <unistd.h>

#include "papi.h"

using namespace std;

class pmc
{
    int verbose= 1;
public:
    pmc(int verbose)
    {
        this->verbose= verbose;
        int EventSet= PAPI_NULL;
        if(PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT)
            throw "Error on init papi";
    }
    void enable_multiplexing()
    {
        if(PAPI_multiplex_init() != PAPI_OK)
            throw "Error on enable multiplexing";
    }
    vector<PAPI_component_info_t> get_components()
    {
        vector<PAPI_component_info_t> components;
        const PAPI_component_info_t *cmpinfo = NULL;
        int numcmp = PAPI_num_components();
        for (int cid = 0; cid < numcmp; cid++)
        {
            if((cmpinfo = PAPI_get_component_info(cid)) == NULL)
                cerr << "Error on get_component_info " << cmpinfo->name;
            if(cmpinfo->disabled)
                cerr <<  "RAPL component disabled " << cmpinfo->disabled_reason << endl;
            components.push_back(*cmpinfo);
            if(verbose > 1) 
                cout << "Found " << cmpinfo->name << " " << PAPI_num_cmp_hwctrs(cid) << " events " << endl;
        }
        return components;
    }
    vector<PAPI_event_info_t> query_events(int cid, int mask_ev)
    {
        vector<PAPI_event_info_t> events;
        PAPI_event_info_t evinfo;
        int code =  mask_ev; //PAPI_NATIVE_MASK PAPI_PRESET_MASK
        int r = PAPI_enum_cmp_event(&code, PAPI_ENUM_FIRST, cid);
        while (r == PAPI_OK)
        {
            if (PAPI_get_event_info(code, &evinfo) != PAPI_OK)
                cerr <<  "Error getting event info" << endl;
            events.push_back(evinfo);
            if(verbose > 1) 
                cout << evinfo.symbol << endl;
            r = PAPI_enum_cmp_event(&code, PAPI_ENUM_EVENTS, cid);
        }
        return events;
    }
    vector<PAPI_event_info_t> query_events(int mask_ev)
    {
        vector<PAPI_event_info_t> events;
        PAPI_event_info_t evinfo;
        int code =  mask_ev; //PAPI_NATIVE_MASK PAPI_PRESET_MASK
        int r = PAPI_enum_event(&code, PAPI_ENUM_FIRST);
        while (r == PAPI_OK)
        {
            if (PAPI_get_event_info(code, &evinfo) != PAPI_OK)
                cerr <<  "Error getting event info" << endl;
            events.push_back(evinfo);
            if(verbose > 1) 
                cout << evinfo.symbol << endl;
            r = PAPI_enum_event(&code, PAPI_ENUM_EVENTS);
        }
        return events;
    }
    // TODO: finish
    void create_eventsets_from_query()
    {
        PAPI_event_info_t evinfo;
        int code =  PAPI_NATIVE_MASK; //PAPI_NATIVE_MASK PAPI_PRESET_MASK
        int r = PAPI_enum_event(&code, PAPI_ENUM_FIRST);
        int EventSet= PAPI_NULL;
        if(PAPI_create_eventset(&EventSet) != PAPI_OK)
            cerr << "Error creating event set" << endl;
        while (r == PAPI_OK)
        {
            if (PAPI_get_event_info(code, &evinfo) != PAPI_OK)
                cerr <<  "Error getting event info" << endl;
            int ret= PAPI_add_event(EventSet, code);
            if (ret != PAPI_OK)
            {
                //   cerr << "Error adding event " << evinfo.symbol  << " reason " << ret << endl;
            }
            else
                cout << "Sucessful add " << evinfo.symbol << endl;
            r = PAPI_enum_event(&code, PAPI_ENUM_EVENTS);
        }
    }
    // BUG : event_codes are wrong for native
    vector<int> create_eventsets_from_types(vector<PAPI_event_info_t> events)
    {
        vector<int> EventSets;
        map<int,vector<int>> clusters;
        for(const auto& e: events)
            clusters[e.event_type].push_back(e.event_code);
        for(const auto& c : clusters)
        {
            int EventSet= PAPI_NULL, code;
            if(PAPI_create_eventset(&EventSet) != PAPI_OK)
                cerr << "Error creating event set" << endl;
            else
            {
                if(verbose > 1) cout << "Trying to create event set code number " << c.first << " with "<< endl;
                for(auto v: c.second)
                {
                    // PAPI_event_name_to_code(v.data(),&code);
                    int ret= PAPI_add_event(EventSet, v);
                    if(verbose > 1) 
                    {
                        char ev_name[128];
                        PAPI_event_code_to_name(v, ev_name);
                        if (ret != PAPI_OK)
                            cerr << "Error adding event " << ev_name << " reason " << ret << endl;
                        else
                            cout << "Sucessful add " << ev_name << endl;
                    }
                }
                if(PAPI_num_events(EventSet) > 0)
                    EventSets.push_back(EventSet);
                if(verbose > 1) cout << "Event set with " << PAPI_num_events(EventSet) << " events " << endl << endl;
            }
        }
        if(verbose > 0) cout << "Created " << EventSets.size() << " Event sets " << endl;
        return EventSets;
    }
    int create_eventset_from_code(vector<int> events)
    {
        int EventSet= PAPI_NULL, code;
        if(PAPI_create_eventset(&EventSet) != PAPI_OK)
            cerr << "Error creating event set" << endl;
        // PAPI_set_multiplex(EventSet);
        for(const auto& ev : events)
        {
            int ret= PAPI_add_event(EventSet, ev);
            if(verbose > 1) 
            {
                char ev_name[128];
                PAPI_event_code_to_name(ev, ev_name);
                if (ret != PAPI_OK)
                    cerr << "Error adding event " << ev_name  << " reason " << ret << endl;
                else
                    cout << "Sucessful add " << ev_name << endl;
            }
        }
        return EventSet;
    }
    void show_events(vector<int> EventSets)
    {
        for(auto e: EventSets)
        {
            cout << "Event " << e << endl;
            int evs[20], n= 20;
            PAPI_list_events(e, evs, &n);
            for(int i=0; i<n; i++)
            {
                char name[128];
                PAPI_event_code_to_name(evs[i], name);
                cout << name << endl;
            }
        }
    }
};


int create_workload(char**argv)
{
    pid_t pid= fork();
    if(pid == 0)
    {
        int fd= open("output", O_WRONLY | O_CREAT, S_IRUSR | S_IWUSR);
        dup2(fd, STDOUT_FILENO);
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        // flush_cache();
        int ret= execl(argv[1], (const char*)argv+1, NULL);
        if(ret < 0)
            cerr << "ERROR ON EXECL " << argv[1] << endl;
    }
    return pid;
}

int main(int argc, char**argv)
{
    try
    {
        pmc p(1);
        // p.enable_multiplexing();
        // vector<PAPI_component_info_t> componetns= p.get_components();

        vector<PAPI_event_info_t> preset_event= p.query_events(PAPI_PRESET_MASK);
        vector<int> EventSets_preset= p.create_eventsets_from_types(preset_event);
        
        int cont=0;
        for(auto ev: EventSets_preset)
        {
            int status;
            int n_evs= PAPI_num_events(ev);
            vector<vector<long long>> samples;
            vector<long long> couters(n_evs);
            vector<long long> tss(n_evs);
            long long *couters2= new long long[n_evs];
            for(int i=0; i<n_evs; i++)
                couters[i]= 0;
            pid_t pid= create_workload(argv);
            if(PAPI_attach(ev, pid) != PAPI_OK)
                cerr << "Erro on attach to pid" << endl;
            waitpid(pid, &status, 0);
            PAPI_start(ev);
            ptrace(PTRACE_CONT, pid, 0, 0);
            usleep(1e3);
            PAPI_read(ev, couters.data());
            // PAPI_reset(ev);
            samples.push_back(couters);
            while(1)
            {
                // cout << ".";
                // cout.flush();
                waitpid(pid, &status, WNOHANG);
                if (WIFEXITED(status))
                    break;
                usleep(1e3);
                PAPI_read(ev, couters.data());
                // PAPI_reset(ev);
                samples.push_back(couters);
            }
            // PAPI_reset(ev);
            int evs[n_evs], n= n_evs;
            PAPI_list_events(ev, evs, &n);
            for(int i=0; i<n; i++)
            {
                char name[128];
                PAPI_event_code_to_name(evs[i], name);
                cout << name << " ";
                cont++;
            }
            cout << endl;
            for(auto s: samples)
            {
                for(auto c: s)
                    cout << c << " ";
                cout << endl;
            }
            cout << endl;
        }
        cout << cont << endl;

        // p.show_events(EventSets_preset);

        // vector<PAPI_event_info_t> native_event= p.query_events(PAPI_NATIVE_MASK);
        // vector<int> EventSets_native= p.create_eventsets_from_types(native_event);
        // p.show_events(EventSets_native);

        // p.create_eventsets_from_query();

        // int my_ev = p.create_eventset_from_code({PAPI_TOT_INS, PAPI_L1_ICM, PAPI_BR_MSP, 
        //                                         PAPI_L3_TCR, PAPI_FP_OPS, PAPI_BR_PRC});
        // int n_evs= PAPI_num_events(my_ev);
        // long long *couters= new long long[n_evs];
        // PAPI_start(my_ev);


        // PAPI_stop(my_ev, couters);
        // PAPI_read(my_ev, couters);
        // int evs[n_evs], n= n_evs;
        // PAPI_list_events(my_ev, evs, &n);
        // for(int i=0; i<n; i++)
        // {
        //     char name[128];
        //     PAPI_event_code_to_name(evs[i], name);
        //     cout << name << " " << couters[i] << endl;
        // }
        
        // p.enable_multiplexing();
        // vector<PAPI_event_info_t> preset_event= p.query_events(PAPI_PRESET_MASK);
        // vector<int> codes;
        // for(const auto& ev: preset_event)
        //     codes.push_back(ev.event_code);
        
        // int cont= 0;
        // for(int i=0; i<codes.size(); i+=7)
        // {
        //     vector<int> aux(codes.begin()+i,codes.begin()+i+6);
        //     cout << &aux[0] << " " << &aux.back() << endl;
        //     int my_ev = p.create_eventset_from_code(aux);
        //     int n_evs= PAPI_num_events(my_ev);
        //     long long *couters= new long long[n_evs];
        //     float x=2.20;
        //     PAPI_start(my_ev);
        //     x= x*x*x*x*x;

        //     PAPI_stop(my_ev, couters);
        //     PAPI_read(my_ev, couters);
        //     int evs[n_evs], n= n_evs;
        //     PAPI_list_events(my_ev, evs, &n);
        //     for(int i=0; i<n; i++)
        //     {
        //         char name[128];
        //         PAPI_event_code_to_name(evs[i], name);
        //         cout << name << " " << couters[i] << endl;
        //         cont++;
        //     }
        // }
        // cout << cont << endl;
    }
    catch(const char* e)
    {
        cout << e << endl;
    }
}