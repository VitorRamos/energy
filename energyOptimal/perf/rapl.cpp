
#include "rapl.h"

#include <iostream>

#include <linux/perf_event.h>
#include <asm/unistd.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <memory.h>

using namespace std;

void RAPL::detect_packages()
{
    string filename;
    FILE *fd;
    int package, i;
    for(i=0;i<128;i++) {
        filename= "/sys/devices/system/cpu/cpu"+to_string(i)+"/topology/physical_package_id";
        fd=fopen(filename.c_str(),"r");
        if(fd==NULL)
            break;
        fscanf(fd,"%d",&package);
        fclose(fd);
        if(package_map.find(package) == package_map.end())
            package_map[package]=i;
    }
    // cout << "Detected "<< i << " cores and " << package_map.size() << " packges" << endl;
    fds.resize(package_map.size());
}
void RAPL::detect_rapl_events()
{
    rapl_ev aux;
    string rapl_domain_names[]= {
        "energy-cores",
        "energy-gpu",
        "energy-pkg",
        "energy-ram",
        "energy-psys",
    };
    FILE* fd= fopen("/sys/bus/event_source/devices/power/type", "r");
    if (fd == NULL)
        cerr << "Error opening event \n";
    fscanf(fd, "%d", &type);
    fclose(fd);
    // cout << "Power eventy type " << type << endl;
    for(const auto& rapl: rapl_domain_names)
    {
        aux.name= rapl;
        string filename= "/sys/bus/event_source/devices/power/events/"+rapl;
        fd= fopen(filename.c_str(), "r");
        if (fd != NULL) {
            fscanf(fd,"event=%x",&aux.config);
            fclose(fd);
            // cout << "Event " << rapl << " Config " << aux.config << " ";
        } else {
            continue;
        }
        filename= "/sys/bus/event_source/devices/power/events/"+rapl+".scale";
        fd= fopen(filename.c_str(), "r");
        if (fd!=NULL) {
            fscanf(fd,"%lf",&aux.scale);
            fclose(fd);
            // cout << "Scale " << aux.scale << " ";
        }
        filename= "/sys/bus/event_source/devices/power/events/"+rapl+".unit";
        fd= fopen(filename.c_str(), "r");
        if (fd!=NULL) {
            aux.unit.resize(128);
            fscanf(fd,"%s",&aux.unit[0]);
            fclose(fd);
            // cout << "Units " << aux.unit << endl;
        }
        rapl_evs.push_back(aux);
    }
}
void RAPL::create_event_set()
{
    for(int i=0; i<package_map.size(); i++)
    {
        for(int j=0; j<rapl_evs.size(); j++)
        {
            perf_event_attr attr;
            memset(&attr,0x0,sizeof(attr));
            attr.type=type;
            attr.config=rapl_evs[j].config;
            int fd= syscall(__NR_perf_event_open, &attr, -1, package_map[i], -1, 0);
            if(fd < 0)
                cerr << "Error creating event" << endl;
            fds[i].push_back(fd);
        }
    }
}
void RAPL::sample()
{
    int64_t value;
    vector<double> row;
    row.resize(rapl_evs.size(), 0);
    for(int i=0; i<package_map.size(); i++)
    {
        for(int j=0; j<rapl_evs.size(); j++)
        {
            read(fds[i][j],&value,8);
            ioctl(fds[i][j], PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
            row[j]+=value*rapl_evs[j].scale;
            // cout << rapl_evs[j].name << " " << value*rapl_evs[j].scale  << " " << rapl_evs[j].unit << endl;
        }
    }
    samples.push_back(row);
}
ostream& RAPL::to_csv(ostream& out)
{
    for(int j=0; j<rapl_evs.size(); j++)
    {
        out << rapl_evs[j].name;
        if(j != rapl_evs.size()-1)
                out << ",";
    }
    out << endl;
    for(const auto& s: samples)
    {
        for(int j=0; j<rapl_evs.size(); j++)
        {
            out << s[j];
            if(j != rapl_evs.size()-1)
                out << ",";
        }
        out << endl;
    }
    return out;
}
void RAPL::delete_samples()
{
    samples.clear();
}
RAPL::RAPL()
{
    detect_packages();
    detect_rapl_events();
    create_event_set();
}
RAPL::~RAPL()
{
    for(int i=0; i<package_map.size(); i++)
        for(int j=0; j<rapl_evs.size(); j++)
            close(fds[i][j]);
}