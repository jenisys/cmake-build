/**
 * @file
 * Provides simple responder class.
 * @note REQUIRES: STD-C++11 or newer
 **/

// -- LOCAL-INCLUDES:
#include "Responder.hpp"
// -- INCLUDES:
#include <sstream>  //< USE: std::ostringstream

namespace hello {

/**
 * Default/InitCtor
 **/
Responder::Responder(const char* greeting)
    : util::NonCopyable(),
      m_greeting(greeting)
{

}

/**
 * Create the response message for the provided message:
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
 * 
 * @param message   Message to process.
 * @return Response message (as string).
 **/
std::string 
Responder::respond(const std::string& message) const
{
    std::ostringstream captured;
    captured << m_greeting <<" "<< message << std::ends;
    return captured.str();
}

} //< NAMESPACE-END: hello
