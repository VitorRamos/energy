#include <iostream>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <papi.h>
#include <vector>

using namespace std;

class RAPL
{
    int rapl_id, EventSet = PAPI_NULL;
    vector<PAPI_event_info_t> infos;
    vector<string> names;
    vector<long long> values;
    double before_time, after_time, elapsed_time;
    int verbose= 0;
private:
    int get_rapl_id()
    {
        const PAPI_component_info_t *cmpinfo = NULL;
        int numcmp = PAPI_num_components(), rapl_cid= -1;
        for (int cid = 0; cid < numcmp; cid++)
        {
            if((cmpinfo = PAPI_get_component_info(cid)) == NULL)
                return -1;
            if(string(cmpinfo->name) ==  "rapl") 
            {
                if(verbose > 1) cout << "Found RAPL" << endl;
                rapl_cid = cid;
                if (cmpinfo->disabled)
                {
                    throw "RAPL component disabled " + string(cmpinfo->disabled_reason);
                    return -1;
                }
                break;
            }
        }
        return rapl_cid;
    }
    void add_rapl_events()
    {
        int code = PAPI_NATIVE_MASK;
        int r = PAPI_enum_cmp_event(&code, PAPI_ENUM_FIRST, rapl_id);
        while (r == PAPI_OK)
        {
            PAPI_event_info_t evinfo;
            char ev_name[128];
            if (PAPI_event_code_to_name(code, ev_name) != PAPI_OK)
                throw "Error translating " + to_string(code);
            names.push_back(ev_name);
            if(verbose > 1)  cout << ev_name << endl;
            if (PAPI_get_event_info(code, &evinfo) != PAPI_OK)
                throw  "Error getting event info";
            infos.push_back(evinfo);
            if (PAPI_add_event(EventSet, code) != PAPI_OK)
                break;
            r = PAPI_enum_cmp_event(&code, PAPI_ENUM_EVENTS, rapl_id);
        }
        values.resize(infos.size());
    }
public:
    RAPL()
    {
        if( PAPI_library_init(PAPI_VER_CURRENT) != PAPI_VER_CURRENT )
            throw "Error on init lib";

        if( (rapl_id= get_rapl_id()) == -1 )
            throw "Error on load rapl";

        if (PAPI_create_eventset(&EventSet) != PAPI_OK)
            throw "Error on create event set";
        
        add_rapl_events();
    }
    void start()
    {
        if(verbose) cout << "Starting measurements..." << endl;
        before_time = PAPI_get_real_nsec();
        if(PAPI_start(EventSet) != PAPI_OK)
            throw "Error on start";
    }
    void stop()
    {
        after_time = PAPI_get_real_nsec();
        if (PAPI_stop(EventSet, values.data()) != PAPI_OK)
            throw "Error on stop";
        elapsed_time = ((double)(after_time - before_time)) / 1.0e9;
        if(verbose) cout << "Stopping measurements, took " << elapsed_time  << ", gathering results..." << endl;
    }
    double get_energy()
    {
        double tot=0;
        cout << "Scaled energy measurements:" << endl;
        for (int i=0; i<infos.size(); i++)
        {
            if( string(infos[i].units).find("nJ") != string::npos)
            {
                if(names[i].find("PACKAGE_ENERGY") != string::npos)
                {
                    tot+=(double)values[i]/1.0e9;
                }
                // cout << names[i] << " " <<  << " " << ((double)values[i]/1.0e9)/elapsed_time << endl;
            }
        }
        return tot;
    }
};


int main(int argc, char **argv)
{
    try
    {
        RAPL rapl;
        for(int i=0; i<100000; i++)
        {
            rapl.start();
            usleep(1e5);
            rapl.stop();
            cout << rapl.get_energy() << endl;
        }
    }
    catch(const char* e)
    {
        cout << e << endl;
    }
    catch(string e)
    {
        cout << e << endl;
    }

    // cout << "\nEnergy measurement counts:\n";
    // for(int i=0; i<infos.size(); i++)
    // {
    //     if (names[i].find("ENERGY_CNT") != string::npos)
    //     {
    //         cout << names[i] << " " <<  values[i] << endl;
    //     }
    // }

    // cout << "\nScaled Fixed values:\n";
    // for(int i=0; i<infos.size(); i++)
    // {
    //     if (names[i].find("ENERGY") == string::npos)
    //     {
    //         if (infos[i].data_type == PAPI_DATATYPE_FP64)
    //         {
    //             union {
    //                 long long ll;
    //                 double fp;
    //             } result;

    //             result.ll = values[i];
    //             cout << names[i] << " " << result.fp << " " <<  infos[i].units << endl;
    //         }
    //     }
    // }

    // cout << "\nFixed value counts:\n";
    // for(int i=0; i<infos.size(); i++)
    // {
    //     if (names[i].find("ENERGY") == string::npos)
    //     {
    //         if (infos[i].data_type == PAPI_DATATYPE_UINT64)
    //         {
    //             cout << names[i] << " " << values[i]  << endl;
    //         }
    //     }
    // }

    // double max_time;
    // unsigned long long max_value = 0;
    // int repeat;
    // for(int i=0; i<infos.size(); i++)
    // {
    //     if (names[i].find("ENERGY_CNT") != string::npos)
    //     {
    //         if (max_value < (unsigned)values[i])
    //         {
    //             max_value = values[i];
    //         }
    //     }
    // }
    // max_time = elapsed_time * ((double)0xffffffff / (double)max_value);
    // cout << "Approximate time to energy measurement wraparound: " << max_time << " sec or " << max_time/60 << "min.\n";

}