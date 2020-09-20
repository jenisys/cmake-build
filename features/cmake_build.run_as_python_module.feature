Feature: Run cmake-build as python module

  Scenario Outline: Run cmake-build as python module
    When I run "python -mcmake_build <cmdline_options>"
    Then it should pass

    Examples:
      | cmdline_options | Comment |
      | --help          | Show program help text. |
      | -l              | List the available cmake-build tasks (commands). |
      | --version       | Show cmake-build version. |

  Scenario: Run cmake-build --list as python module
    When I run "python -mcmake_build -l"
    Then it should pass with
      """
      Default task: build
      """
    And note that "the following tasks should be described"
    Then the command output should contain "init"
    And  the command output should contain "build"
    And  the command output should contain "test"
    And  the command output should contain "install"
    And  the command output should contain "pack"
    And  the command output should contain "reinit"
    And  the command output should contain "rebuild"
    And  the command output should contain "update"
    And  the command output should contain "clean"
    And  the command output should contain "cleanup"
    And  the command output should contain "cleanup.all"

