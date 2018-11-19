#include <perfmon/pfmlib.h>
#include <perfmon/pfmlib_perf_event.h>
#include <memory.h>

#include <iostream>
#include <algorithm>
#include <string>
#include <map>
#include <tuple>
using namespace std;

class events
{
    map<tuple<uint64_t, uint64_t>, string> evs;
    int generate_header= 1;
public:
    events()
    {
        if (pfm_initialize() != PFM_SUCCESS)
            cerr << "cannot initialize library" << endl;
    }
    int show_event(pfm_event_info_t info)
    {
        int total_working_events= 0;
        pfm_perf_encode_arg_t raw;
        perf_event_attr_t hw;
        pfm_event_attr_info_t att_info;
        memset(&raw, 0, sizeof(raw));
        memset(&hw, 0, sizeof(hw));
        raw.attr= &hw;
        memset(&att_info, 0, sizeof(att_info));
        string str_event= string(info.name);
        if(pfm_get_os_event_encoding(str_event.c_str(), PFM_PLM0 | PFM_PLM3, PFM_OS_PERF_EVENT_EXT, &raw) == PFM_SUCCESS
        && (evs.find(make_tuple(raw.attr->type, raw.attr->config)) == evs.end()) )
        {
            if(generate_header)
            {
                while(str_event.find(':') != string::npos)
                    str_event.replace(str_event.find(':'),1,"_");
                while(str_event.find('-') != string::npos)
                    str_event.replace(str_event.find('-'),1,"_");
                cout << "#define " << str_event << "_TYPE " << raw.attr->type << endl;
                cout << "#define " << str_event << "_CONFIG " << raw.attr->config << endl;    
            }
            else
                cout << "\t" << info.name << " " << raw.attr->type << " " << raw.attr->config << endl;
            total_working_events++;
            evs[make_tuple(raw.attr->type, raw.attr->config)]= str_event;
        }
        for(int i=0; i<info.nattrs; i++)
        {
            memset(&raw, 0, sizeof(raw));
            memset(&hw, 0, sizeof(hw));
            raw.attr= &hw;
            memset(&att_info, 0, sizeof(att_info));
            if(pfm_get_event_attr_info(info.idx, i, PFM_OS_NONE, &att_info) == PFM_SUCCESS)
            {
                string str_event= string(info.name)+":"+string(att_info.name);
                if(pfm_get_os_event_encoding(str_event.c_str(), PFM_PLM0 | PFM_PLM3, PFM_OS_PERF_EVENT_EXT, &raw) == PFM_SUCCESS)
                {
                    if(evs.find(make_tuple(raw.attr->type, raw.attr->config)) != evs.end())
                        continue;
                    if(generate_header)
                    {
                        while(str_event.find(':') != string::npos)
                            str_event.replace(str_event.find(':'),1,"_");
                        while(str_event.find('-') != string::npos)
                            str_event.replace(str_event.find('-'),1,"_");
                        cout << "#define " << str_event << "_TYPE " << raw.attr->type << endl;
                        cout << "#define " << str_event << "_CONFIG " << raw.attr->config << endl;    
                    }
                    else
                        cout << "\t" << info.name << " " << raw.attr->type << " " << raw.attr->config << endl;
                    total_working_events++;
                    if(evs.find(make_tuple(raw.attr->type, raw.attr->config)) == evs.end())
                        evs[make_tuple(raw.attr->type, raw.attr->config)]= str_event;
                }
            }
        }
        return total_working_events;
    }
    int list_pmu_events(pfm_pmu_t pmu)
    {
        int i, ret, total_working_configs= 0, total_working_events= 0;
        pfm_event_info_t info;
        pfm_pmu_info_t pinfo;
        memset(&info, 0, sizeof(info));
        memset(&pinfo, 0, sizeof(pinfo));
        info.size = sizeof(info);
        pinfo.size = sizeof(pinfo);

        if (pfm_get_pmu_info(pmu, &pinfo) != PFM_SUCCESS)
            cerr << "cannot get pmu info" << endl;

        for (i = pinfo.first_event; i != -1; i = pfm_get_event_next(i))
        {
            if (pfm_get_event_info(i, PFM_OS_PERF_EVENT, &info) != PFM_SUCCESS)
                cerr << "cannot get event info" << endl;
            if(pinfo.is_present)
            {
                total_working_configs+=show_event(info);
                total_working_events+= total_working_configs > 0;
            }
        }
        return total_working_configs;
    }
    void supported_pmus()
    {
        pfm_pmu_info_t pinfo;
        memset(&pinfo, 0, sizeof(pinfo));
        cout << "Supported pmu models" << endl;
        for(int i=PFM_PMU_NONE; i<PFM_PMU_MAX; i++)
        {
            if (pfm_get_pmu_info(pfm_pmu_t(i), &pinfo) != PFM_SUCCESS)
                continue;
            cout << pinfo.name << " " << pinfo.desc << endl;
        }
    }
    void detected_pmus()
    {
        int total_supported_events=0, total_available_events=0, total_working_events=0, total_pmus= 0;
        pfm_pmu_info_t pinfo;
        memset(&pinfo, 0, sizeof(pinfo));
        if(generate_header) cout << "// ";
        cout << "Supported pmu models" << endl;
        for(int i=PFM_PMU_NONE; i<PFM_PMU_MAX; i++)
        {
            if (pfm_get_pmu_info(pfm_pmu_t(i), &pinfo) != PFM_SUCCESS)
                continue;
            if(pinfo.is_present)
            {
                total_pmus++;
                total_supported_events+= pinfo.nevents;
                if(generate_header) cout << "// ";
                cout << pinfo.name << " " << pinfo.desc << " " << pinfo.nevents << endl;
                total_working_events+=list_pmu_events(pfm_pmu_t(i));
            }
            total_available_events+=pinfo.nevents;
        }
        if(generate_header) cout << "// ";
        cout << total_pmus << " pmus, supported " << total_working_events << " events" << endl;
    }
    
};

int main()
{
    events e;
    //e.supported_pmus();
    e.detected_pmus();
    // e.list_pmu_events(PFM_PMU_INTEL_SNB_EP);
}