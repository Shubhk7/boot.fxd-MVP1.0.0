#include "../include/baseline.h"

#include <fstream>

using namespace std;


bool save_baseline(
    const map<string, string>& hashes,
    const string& filename)
{
    try
    {
        ofstream file(filename);

        if (!file)
            return false;

        file << "{\n";

        size_t count = 0;

        for (const auto& pair : hashes)
        {
            file << "  \"" << pair.first
                 << "\": \"" << pair.second << "\"";

            if (++count < hashes.size())
                file << ",";

            file << "\n";
        }

        file << "}\n";

        return true;
    }
    catch (...)
    {
        return false;
    }
}


map<string, string> load_baseline(const string& filename)
{
    map<string, string> hashes;

    try
    {
        ifstream file(filename);

        if (!file)
            return hashes;

        string line;

        while (getline(file, line))
        {
            size_t k1 = line.find('"');
            if (k1 == string::npos) continue;

            size_t k2 = line.find('"', k1 + 1);
            if (k2 == string::npos) continue;

            string key = line.substr(k1 + 1, k2 - k1 - 1);

            size_t v1 = line.find('"', k2 + 1);
            if (v1 == string::npos) continue;

            size_t v2 = line.find('"', v1 + 1);
            if (v2 == string::npos) continue;

            string value = line.substr(v1 + 1, v2 - v1 - 1);

            hashes[key] = value;
        }
    }
    catch (...)
    {
    }

    return hashes;
}