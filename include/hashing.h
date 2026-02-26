#pragma once

#include <cstddef>
#include <filesystem>
#include <string>
#include <vector>

namespace bootfxd {

constexpr std::size_t kSha256HexLength = 64;

// Returns SHA-256 hash (hex encoded) of an in-memory byte buffer.
std::string sha256Buffer(const std::vector<unsigned char>& data);

// Returns SHA-256 hash (hex encoded) of raw bytes.
std::string sha256Bytes(const unsigned char* data, std::size_t length);

// Computes SHA-256 hash (hex encoded) for a file in binary mode.
// Returns true on success; false when the file cannot be read.
bool sha256File(const std::filesystem::path& filePath,
                std::string& outHash,
                std::string& outError);

// Reads first `byteCount` bytes from `filePath`.
// Returns true on success; false if file cannot be read or is too small.
bool readFirstBytes(const std::filesystem::path& filePath,
                    std::size_t byteCount,
                    std::vector<unsigned char>& outBytes,
                    std::string& outError);

// Reads first 512 bytes from disk device path and returns SHA-256 hash.
// Intended for BIOS mode MBR measurement (e.g., /dev/sda).
bool sha256Mbr(const std::filesystem::path& devicePath,
               std::string& outHash,
               std::string& outError);

}  // namespace bootfxd