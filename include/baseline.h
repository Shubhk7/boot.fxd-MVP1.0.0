#ifndef BASELINE_H
#define BASELINE_H

#include <map>
#include <string>

/*
 Baseline Module

 Responsibilities:

 - Save baseline hashes to file
 - Load baseline hashes from file

 File location:
    output/baseline.json
*/

bool save_baseline(
    const std::map<std::string, std::string>& hashes,
    const std::string& filename);

std::map<std::string, std::string> load_baseline(
    const std::string& filename);

#endif