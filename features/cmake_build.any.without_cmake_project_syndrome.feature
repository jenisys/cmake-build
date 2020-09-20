@smoke
Feature: Directory is not a CMake Project (Syndrome)

  SYNDROME: CMakeLists.txt file is missing

  As a cmake-build user
  I want that common syndromes are handled in a uniform way (for all commands)
  So that ...

  Scenario Outline: Not a CMake project syndrome with "cmake-build <Command>"
    Given a new working directory
    When I run "cmake-build <Command>"
    Then it should <Outcome> with
      """
      CMAKE-BUILD: Ignore . (not a cmake.project; cwd={__WORKDIR__})
      """

    Examples: Failing commands
      | Command | Outcome |
      | init    | fail    |
      | build   | fail    |
      | test    | fail    |
      | install | fail    |
      | pack    | fail    |
      | rebuild | fail    |
      | reinit  | fail    |
      | update  | fail    |
      | clean   | fail    |

    Examples: Passing commands
      | Command     | Outcome |
      | cleanup     | pass    |
      | cleanup.all | pass    |
