#ifndef COMPARE_H
#define COMPARE_H

#include <map>
#include <string>
#include <vector>

/*
 Compare Module

 Responsibilities:

 - Compare baseline hashes vs current hashes
 - Detect:

    MODIFIED files
    NEW files
    MISSING files

*/


struct CompareResult
{
    std::vector<std::string> modified;
    std::vector<std::string> added;
    std::vector<std::string> removed;

    bool clean = true;
};



//  Compare baseline and current hashes

//  Returns CompareResult struct

CompareResult compare_hashes(
    const std::map<std::string, std::string>& baseline,
    const std::map<std::string, std::string>& current);

#endif