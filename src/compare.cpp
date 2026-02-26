#include "../include/compare.h"

using namespace std;


CompareResult compare_hashes(
    const map<string, string>& baseline,
    const map<string, string>& current)
{
    CompareResult result;

    for (const auto& base : baseline)
    {
        auto it = current.find(base.first);

        if (it == current.end())
        {
            result.removed.push_back(base.first);
            result.clean = false;
        }
        else if (it->second != base.second)
        {
            result.modified.push_back(base.first);
            result.clean = false;
        }
    }

    for (const auto& curr : current)
    {
        if (baseline.find(curr.first) == baseline.end())
        {
            result.added.push_back(curr.first);
            result.clean = false;
        }
    }

    return result;
}