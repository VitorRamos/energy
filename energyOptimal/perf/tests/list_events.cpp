#include <perfmon/pfmlib.h>
#include <perfmon/pfmlib_perf_event.h>
#include <memory.h>

#include <iostream>
using namespace std;

class events
{
    public:
    events()
    {
        if (pfm_initialize() != PFM_SUCCESS)
            cerr << "cannot initialize library" << endl;
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
        cout << "Supported pmu models" << endl;
        for(int i=PFM_PMU_NONE; i<PFM_PMU_MAX; i++)
        {
            if (pfm_get_pmu_info(pfm_pmu_t(i), &pinfo) != PFM_SUCCESS)
                continue;
            if(pinfo.is_present)
            {
                total_pmus++;
                total_supported_events+= pinfo.nevents;
                cout << pinfo.name << " " << pinfo.desc << " " << pinfo.nevents << endl;
                total_working_events+=list_pmu_events(pfm_pmu_t(i));
            }
            total_available_events+=pinfo.nevents;
        }
        cout << total_pmus << " pmus, supported " << total_working_events << " events" << endl;
    }
    int list_pmu_events(pfm_pmu_t pmu)
    {
        int i, ret, total_working_events= 0;
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
                pfm_perf_encode_arg_t raw;
                perf_event_attr_t hw;
                memset(&raw, 0, sizeof(raw));
                memset(&hw, 0, sizeof(hw));
                raw.attr= &hw;
                pfm_get_os_event_encoding(info.name, PFM_PLM0 | PFM_PLM3, PFM_OS_PERF_EVENT_EXT, &raw);
                cout << "\t" << info.name << " " << raw.attr->type << " " << raw.attr->config << endl;
                total_working_events++;
            }
        }
        return total_working_events;
    }
};

int main()
{
    events e;
    e.supported_pmus();
    e.detected_pmus();
    e.list_pmu_events(PFM_PMU_INTEL_RAPL);
}