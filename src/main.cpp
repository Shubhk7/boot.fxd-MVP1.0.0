#include "../include/scanner.h"
#include "../include/baseline.h"
#include "../include/compare.h"

#include <iostream>
#include <filesystem>

using namespace std;

const string BASELINE_FILE = "output/baseline.json";


void print_clean()
{
    cout << "{ \"status\": \"clean\" }\n";
}


void print_error(const string& msg)
{
    cout << "{ \"status\": \"error\", \"message\": \"" << msg << "\" }\n";
}


void print_tampered(const CompareResult& r)
{
    cout << "{\n";
    cout << "\"status\":\"tampered\",\n";

    auto print_vec = [](const string& name,
                        const vector<string>& v,
                        bool comma)
    {
        cout << "\"" << name << "\":[";

        for (size_t i = 0; i < v.size(); i++)
        {
            cout << "\"" << v[i] << "\"";
            if (i + 1 < v.size()) cout << ",";
        }

        cout << "]";

        if (comma) cout << ",";

        cout << "\n";
    };

    print_vec("modified", r.modified, true);
    print_vec("added", r.added, true);
    print_vec("removed", r.removed, false);

    cout << "}\n";
}


int init_mode()
{
    auto hashes = collect_hashes();

    if (hashes.empty())
    {
        print_error("hash_failed");
        return 1;
    }

    filesystem::create_directory("output");

    if (!save_baseline(hashes, BASELINE_FILE))
    {
        print_error("save_failed");
        return 1;
    }

    cout << "{ \"status\": \"baseline_created\" }\n";

    return 0;
}


int scan_mode()
{
    auto baseline = load_baseline(BASELINE_FILE);

    if (baseline.empty())
    {
        print_error("baseline_missing");
        return 1;
    }

    auto current = collect_hashes();

    CompareResult result =
        compare_hashes(baseline, current);

    if (result.clean)
    {
        print_clean();
        return 0;
    }

    print_tampered(result);

    return 2;
}


int main(int argc, char* argv[])
{
    if (argc != 2)
    {
        print_error("invalid_args");
        return 1;
    }

    string arg = argv[1];

    if (arg == "--init")
        return init_mode();

    if (arg == "--scan")
        return scan_mode();

    print_error("unknown_arg");

    return 1;
}