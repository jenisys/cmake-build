/**
 * @file
 * Provides simple responder class.
 * @note REQUIRES: STD-C++11 or newer
 **/

#pragma once
// -- PRE-C++11 SUPPORT (normally not needed):
#ifndef HELLO_RESPONDER_HPP_DEFINED
#define HELLO_RESPONDER_HPP_DEFINED

// -- INCLUDES:
#include "util/NonCopyable.hpp"
#include <string>   //< USE: std::string

namespace hello {

/**
 * @class Responder
 * Simple responder class.
 * 
 * @par RESPONSIBILITIES and COLLABORATORS
 * - Creates a response message for a request message.
 * - Non-copyable
 * @see hello::NonCopyable
 * 
 * @code
 *      #include "hello/Responder.hpp"
 *      #include <string>
 *      #include <cassert>
 * 
 *      hello::Responder responder("Hello");
 *      std::string response = responder.respond("Alice");
 *      assert(response == "Hello Alice"); 
 * @endcode
 **/
class Responder : private util::NonCopyable
{
private:
    std::string  m_greeting;    //!< Greeting string to use.

public:
    Responder(const char* greeting = "Hello");
    std::string respond(const std::string& message) const;
};

} //< NAMESPACE-END: hello
#endif //< ENDOF: HEADER-FILE (pre-C++11 support)
