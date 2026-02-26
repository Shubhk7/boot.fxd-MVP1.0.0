#ifndef SCANNER_H
#define SCANNER_H

#include <filesystem>
#include <map>
#include <string>

std::string detect_boot_mode();
std::map<std::string, std::string> collect_hashes();
#endif
/*
 Boot Integrity Monitor - Scanner Module

 Responsibilities:
 - Detect boot mode (UEFI or BIOS)
 - Collect hashes of boot-critical components

 This module:
 - Does NOT modify system files
 - Does NOT write output files
 - Only returns collected hashes
*/


/*
 Detect boot mode

 Returns:
    "UEFI" if /sys/firmware/efi exists
    "BIOS" otherwise
*/


/*
 Collect hashes of boot-critical components

 Returns:
    std::map where:

    Key examples:
        EFI:/boot/efi/EFI/ubuntu/grubx64.efi
        BOOT:/boot/grub/grub.cfg
        MBR:/dev/sda

    Value:
        SHA256 hash
*/

