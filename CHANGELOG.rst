CHANGELOG
===============================================================================

Release v0.3.0 (UNRELEASED)
-------------------------------------------------------------------------------

GOALS:

- Drop Python2.7 support.


Release v0.2.0 (UNRELEASED)
-------------------------------------------------------------------------------

FEATURES:

- Support for cmake.generator="ninja.multi" ("Ninja Multi-Config")
- Support for "cmake --config <CONFIG>" added to support
  CMAKE_GENERATOR(s) with multi-configuration support.

- REMEMBER-SETTINGS: Support shared inter-task settings for: config, build_config
  REASON: Simplify reuse of current build context/config in following tasks.
  EXAMPLE: cmake-build build --config=Release test

- Use specialized CMakeBuildTask class now for cmake-build tasks
  to support task-specific option names (cmake_defines, ...)
  and REMEMBER-SETTINGS between cmake-build tasks.

- BUILD_CONFIG_ALIASES: In config-files via "build_config_aliases" (as map).
- Improved placeholder support in cmake-build configurations

BREAKING CHANGES:

- cmdline: Short command-line option for "--define" changed to "-D" (was: "-d").
  REASON: Better support cmake-like command-line options.

- pack command: Option "--config" was renamed to "--cpack-config".
  REASON: Use same name for cmake "--config" option in all tasks.


Release v0.1.20 (2019-12-09)
-------------------------------------------------------------------------------

...
