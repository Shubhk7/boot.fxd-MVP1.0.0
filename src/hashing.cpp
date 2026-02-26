#include "hashing.h"

#include <openssl/sha.h>

#include <fstream>
#include <iomanip>
#include <sstream>

namespace bootfxd {
namespace {

std::string toHexString(const unsigned char* digest, std::size_t length) {
    std::ostringstream oss;
    oss << std::hex << std::setfill('0');

    for (std::size_t i = 0; i < length; ++i) {
        oss << std::setw(2) << static_cast<unsigned int>(digest[i]);
    }

    return oss.str();
}

}  // namespace

std::string sha256Buffer(const std::vector<unsigned char>& data) {
    if (data.empty()) {
        return sha256Bytes(nullptr, 0);
    }
    return sha256Bytes(data.data(), data.size());
}

std::string sha256Bytes(const unsigned char* data, std::size_t length) {
    unsigned char digest[SHA256_DIGEST_LENGTH] = {0};
    SHA256(data, length, digest);
    return toHexString(digest, SHA256_DIGEST_LENGTH);
}

bool sha256File(const std::filesystem::path& filePath,
                std::string& outHash,
                std::string& outError) {
    std::ifstream in(filePath, std::ios::binary);
    if (!in.is_open()) {
        outError = "Failed to open file: " + filePath.string();
        return false;
    }

    SHA256_CTX ctx;
    if (SHA256_Init(&ctx) != 1) {
        outError = "Failed to initialize SHA256 context for: " + filePath.string();
        return false;
    }

    std::vector<char> buffer(8192);
    while (in.good()) {
        in.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
        const std::streamsize bytesRead = in.gcount();

        if (bytesRead > 0) {
            if (SHA256_Update(&ctx, buffer.data(), static_cast<std::size_t>(bytesRead)) != 1) {
                outError = "Failed to update SHA256 for: " + filePath.string();
                return false;
            }
        }
    }

    if (!in.eof()) {
        outError = "Failed while reading file: " + filePath.string();
        return false;
    }

    unsigned char digest[SHA256_DIGEST_LENGTH] = {0};
    if (SHA256_Final(digest, &ctx) != 1) {
        outError = "Failed to finalize SHA256 for: " + filePath.string();
        return false;
    }

    outHash = toHexString(digest, SHA256_DIGEST_LENGTH);
    outError.clear();
    return true;
}

bool readFirstBytes(const std::filesystem::path& filePath,
                    std::size_t byteCount,
                    std::vector<unsigned char>& outBytes,
                    std::string& outError) {
    outBytes.clear();

    std::ifstream in(filePath, std::ios::binary);
    if (!in.is_open()) {
        outError = "Failed to open file: " + filePath.string();
        return false;
    }

    outBytes.resize(byteCount);
    in.read(reinterpret_cast<char*>(outBytes.data()), static_cast<std::streamsize>(byteCount));
    const std::streamsize bytesRead = in.gcount();

    if (bytesRead < static_cast<std::streamsize>(byteCount)) {
        outBytes.clear();
        outError = "File/device smaller than requested bytes: " + filePath.string();
        return false;
    }

    outError.clear();
    return true;
}

bool sha256Mbr(const std::filesystem::path& devicePath,
               std::string& outHash,
               std::string& outError) {
    std::vector<unsigned char> mbrBytes;
    constexpr std::size_t kMbrBytes = 512;

    if (!readFirstBytes(devicePath, kMbrBytes, mbrBytes, outError)) {
        return false;
    }

    outHash = sha256Buffer(mbrBytes);
    outError.clear();
    return true;
}

}  // namespace bootfxd