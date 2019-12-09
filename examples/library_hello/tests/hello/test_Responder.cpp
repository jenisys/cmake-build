// -- SIMPLE TEST PROGRAM: Hello world example
// REQUIRES: C++11

// -- INCLUDES:
#include "hello/Responder.hpp"
#include "util/StringUtil.hpp"
#include <iostream>
#include <sstream>
#include <string>

#if 0
namespace util
{

std::string concat_args(int argc, char **argv)
{
    std::ostringstream captured;

    for (int i = 1; i < argc; ++i)
    {
        const char *arg = argv[i];
        captured << arg << " ";
    }
    return captured.str();
}

} // namespace util
#endif

int main(int argc, char **argv)
{
    hello::Responder responder("Hello");
    std::string args((argc > 1) ? util::concat_args(argc, argv) : "Alice");
    std::string response = responder.respond(args);

    std::cout << "RESPONDER: " << response << std::endl;
    return 0;
}
