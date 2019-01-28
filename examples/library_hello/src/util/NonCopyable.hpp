/**
 * @file
 * Provides simple NonCopyable class.
 * @note REQUIRES: STD-C++11 or newer
 **/

#pragma once
// -- PRE-C++11 SUPPORT (normally not needed):
#ifndef UTIL_NONCOPYABLE_HPP_DEFINED
#define UTIL_NONCOPYABLE_HPP_DEFINED

namespace util {

/**
 * @class NonCopyable
 * Marker class that marks a class as non-copyable.
 * 
 * @code
 *  #include "hello/NonCopyable.hpp"
 *  
 *  class Foo : private hello::NonCopyable
 *  {
 *  };
 * @endcode
 **/
class NonCopyable
{
public:
    NonCopyable(void) {};
    NonCopyable(const NonCopyable& other) = delete;
    NonCopyable& operator=(const NonCopyable& other) = delete;
};

} //< NAMESPACE-END: util
#endif //< ENDOF-HEADER-FILE (pre-C++11 support)
