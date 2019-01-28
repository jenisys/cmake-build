// -- SIMPLE PROGRAM: Hello world example
// REQUIRES: C++11 or newer

#include "hello/Responder.hpp"
#include "util/StringUtil.hpp"
#include <string>
#include <iostream>
#include <cassert>

// ---------------------------------------------------------------------------
// MAIN FUNCTION:
// ---------------------------------------------------------------------------
int main(int argc, char **argv)
{
    hello::Responder responder("Hello");
    std::string args((argc > 1) ? util::concat_args(argc, argv) : "Alice");
    std::string response = responder.respond(args);

    std::cout << "RESPONDER: " << response << std::endl;
    return 0;
}
