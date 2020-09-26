@smoke
Feature: CMake Project directory does not exist (Syndrome)

  As a cmake-build user
  I want that common syndromes are handled in a uniform way (for all commands)
  So that ...

  # MAYBE: Given I use the current directory as working directory

  Scenario Outline: Non-existing directory syndrome with "cmake-build <Command>"
    Given a new working directory
    When I run "cmake-build <Command> --project=NON_EXISTING_DIR"
    Then it should <Outcome> with
      """
      CMAKE-<COMMAND>: NON_EXISTING_DIR (SKIPPED: cmake.project directory does not exist)
      """

    Examples: Failing commands
      | Command   | COMMAND   | Outcome |
      | init      | INIT      | fail    |
      | build     | BUILD     | fail    |
      | test      | TEST      | fail    |
      | install   | INSTALL   | fail    |
      | pack      | PACK      | fail    |
      | rebuild   | BUILD     | fail    |
      | reinit    | INIT      | fail    |
      | configure | CONFIGURE | fail    |

    Examples: Passing commands
      | Command   | COMMAND   | Outcome |
      | clean     | CLEAN     | pass    |
