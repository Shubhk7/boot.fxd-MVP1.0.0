#include "../include/scanner.h"
#include "../include/hashing.h"

#include <filesystem>
#include <fstream>

using namespace std;
using namespace bootfxd;

namespace fs = std::filesystem;


/*
 Recursively hash all regular files in directory
*/
static void hash_directory(
    const string& prefix,
    const fs::path& directory,
    map<string, string>& hashes)
{
    try
    {
        if (!fs::exists(directory))
            return;

        for (const auto& entry :
             fs::recursive_directory_iterator(
                 directory,
                 fs::directory_options::skip_permission_denied))
        {
            try
            {
                if (entry.is_regular_file())
                {
                    string hash;
                    string error;

                    if (sha256File(entry.path(), hash, error))
                    {
                        hashes[prefix + entry.path().string()] = hash;
                    }
                }
            }
            catch (...)
            {
                // skip unreadable files safely
                continue;
            }
        }
    }
    catch (...)
    {
        // skip inaccessible directories safely
    }
}


/*
 Detect boot mode
*/
string detect_boot_mode()
{
    try
    {
        if (fs::exists("/sys/firmware/efi"))
            return "UEFI";
    }
    catch (...)
    {
    }

    return "BIOS";
}


/*
 Hash MBR using proper hashing API
*/
static string hash_mbr()
{
    try
    {
        string hash;
        string error;

        if (sha256Mbr("/dev/sda", hash, error))
        {
            return hash;
        }
    }
    catch (...)
    {
    }

    return "";
}


/*
 Collect hashes of boot-critical components
*/
map<string, string> collect_hashes()
{
    map<string, string> hashes;

    string mode = detect_boot_mode();


    // UEFI mode
    if (mode == "UEFI")
    {
        hash_directory(
            "EFI:",
            "/boot/efi/EFI/",
            hashes);
    }
    else
    {
        // BIOS mode → hash MBR
        string mbr_hash = hash_mbr();

        if (!mbr_hash.empty())
        {
            hashes["MBR:/dev/sda"] = mbr_hash;
        }
    }


    // Hash GRUB directories (both modes)
    hash_directory(
        "BOOT:",
        "/boot/grub/",
        hashes);

    hash_directory(
        "BOOT:",
        "/boot/grub2/",
        hashes);


    return hashes;
}