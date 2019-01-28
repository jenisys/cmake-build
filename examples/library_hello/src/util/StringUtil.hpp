/**
 * @file
 * Provides string/cstring utilities.
 * @note REQUIRES: STD-C++11 or newer
 **/

#pragma once
// -- PRE-C++11 SUPPORT (normally not needed):
#ifndef UTIL_STRINGUTIL_HPP_DEFINED
#define UTIL_STRINGUTIL_HPP_DEFINED

#include <sstream>  //< USE: std::stringstream

namespace util {

inline std::string concat_args(int argc, char** argv)
{
    std::ostringstream captured;

    for (int i = 1; i < argc; ++i)
    {
        const char *arg = argv[i];
        captured << arg << " ";
    }
    return captured.str();
}

} //< NAMESPACE-END: util
#endif //< ENDOF-HEADER-FILE (pre-C++11 support)
