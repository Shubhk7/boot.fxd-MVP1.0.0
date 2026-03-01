#ifndef SCANNER_H
#define SCANNER_H

#include <filesystem>
#include <map>
#include <string>

//  Boot Integrity Monitor - Scanner Module
std::string detect_boot_mode(); //to detect if boot mode is UEFI or BIOS


// Collect hashes of boot-critical components
std::map<std::string, std::string> collect_hashes();
#endif
