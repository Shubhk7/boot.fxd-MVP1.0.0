#include "../include/scanner.h"
#include "../include/hashing.h"

#include <filesystem>
#include <fstream>

using namespace std;
namespace fs = std::filesystem;


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
                    string path = entry.path().string();

                    string hash = sha256_file(path);

                    if (!hash.empty())
                        hashes[prefix + path] = hash;
                }
            }
            catch (...)
            {
                continue;
            }
        }
    }
    catch (...)
    {
    }
}


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


static string hash_mbr()
{
    try
    {
        ifstream device("/dev/sda", ios::binary);

        if (!device)
            return "";

        char buffer[512];

        device.read(buffer, 512);

        if (device.gcount() <= 0)
            return "";

        string temp = "/tmp/.bootfxd_mbr";

        ofstream tmp(temp, ios::binary);

        if (!tmp)
            return "";

        tmp.write(buffer, device.gcount());
        tmp.close();

        string hash = sha256_file(temp);

        fs::remove(temp);

        return hash;
    }
    catch (...)
    {
        return "";
    }
}


map<string, string> collect_hashes()
{
    map<string, string> hashes;

    string mode = detect_boot_mode();

    if (mode == "UEFI")
    {
        hash_directory(
            "EFI:",
            "/boot/efi/EFI/",
            hashes);
    }
    else
    {
        string mbr_hash = hash_mbr();

        if (!mbr_hash.empty())
            hashes["MBR:/dev/sda"] = mbr_hash;
    }

    hash_directory("BOOT:", "/boot/grub/", hashes);
    hash_directory("BOOT:", "/boot/grub2/", hashes);

    return hashes;
}