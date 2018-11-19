#pragma once

#include <vector>
#include <ostream>
#include <map>

class RAPL
{
    struct rapl_ev
    {
        int config;
        double scale;
        std::string unit;
        std::string name;
    };
    int type;
    std::vector<rapl_ev> rapl_evs;
    std::map<int,int> package_map;
    std::vector<std::vector<int>> fds;
    std::vector<std::vector<double>> samples;
private:
    void detect_packages();
    void detect_rapl_events();
    void create_event_set();
public:
    void sample();
    std::ostream& to_csv(std::ostream& out);
    void delete_samples();
    RAPL();
    ~RAPL();
};