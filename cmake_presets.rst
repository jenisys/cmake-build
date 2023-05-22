CMake Presets
===============================================================================

:Requires: cmake >= 3.19
:TODO: Update to newest CMakePresets schema (cmake v3.26.x)

Simplify reproducible bootstrap/init of CMake projects / build system by using
preset-configuration-file(s):

.. code-block:: bash

    # -- INIT BUILD-DIRECTORY "build.default/" with preset="default"
    # DIRECTORY: CMAKE_SOURCE_DIR, where "CMakeLists.txt" file is located.
    $ cmake --preset=default ..

EXAMPLE:

.. code-block:: json

    {
        "version": 1,
        "configurePresets": [
            {
                "name": "default",
                "displayName": "Default Config",
                "description": "Default build using Ninja generator",
                "generator": "Ninja",
                "binaryDir": "${sourceDir}/build.${presetName}",
                "cacheVariables": {
                    "CMAKE_PRESET": "${presetName}",
                    "CMAKE_BUILD_TYPE": "Release",
                    "FIRST_CACHE_VARIABLE": {
                        "type": "BOOL",
                        "value": "OFF"
                    },
                }
            },
            {
                "name": "multi",
                "inherits": "default",
                "generator": "Ninja Multi-Config",
            }
        ]
    }


FILES (colocated to: ``CMakeLists.txt`` file):

* ``CMakePresets.json``     -- project-wide configuration
* ``CMakeUserPresets.json`` -- can inherit presets from: ``CMakePresets.json``; user-specific

SEE ALSO:

* https://cmake.org/cmake/help/v3.19/manual/cmake-presets.7.html


CMake Preset Placeholders
-------------------------------------------------------------------------------

* Use "${placeholder}" to replace with placeholder.value
* Use "$env{environment_variable}" to replace with environment_variable.value
* Use "$penv{environment_variable}" for path-like environment_variables

PLACEHOLDERS:

* sourceDir : path
* sourceParentDir : path
* sourceDirName : path       # dirname(sourceDir), last-part of sourceDir.

* presetName : string
* generator  : string-enum
* dollar : string = "$"
* env{variable_name} : string = ""
* vendor{macro_name}

PLACEHOLDERS CAN BE USED IN:

* configurePresets.<PRESET_NAME>.binaryDir
* configurePresets.<PRESET_NAME>.environment


Data Model
-------------------------------------------------------------------------------

::

    version : Number
    cmakeMinimumRequired : Version
    configurePresets : sequence<PresetObject>
    vendor : Dict

    type Version:
        major : PositiveNumber
        minor : PositiveNumber
        patch : PositiveNumber

    type Preset:
        name : string (id,  key)    # REQUIRED.
        hidden : bool? = false      # Mark abstract-presets.
        inherits : sequence<string> | string?  # Inherited preset-name(s)
        displayName : string?       # Optional human-friendly, readable name.
        description : string?       # Optional description of preset.
        architecture : Toolset?
        generator : string-enum
        binaryDir : string          # Like: "${sourceDir}/build.default"

        cacheVariables : DefinitionsDict
        environment : EnvironmentDict
        warnings : WarningsObject?
        errors : ErrorsObject?
        debug : DebugObject?

        cmakeExecutable : path?
        vendor : Dict?

    type DefinitionsDict(Dict):
        name : value-as-string | { type : string, value : Any }   # VARIANT 1 or 2

    type WarningsObject:
        dev : bool?             # -Wdev or -Wno-dev
        deprecated : bool?      # -Wdeprecated or -Wno-deprecated
        unitialized : bool?     # --warn-unitialized if true
        unusedCli : bool?
        systemVars : bool?      # --check-system-vars if true

    type ErrorsObject:
        dev : bool?             # -Werror=dev or -Wno-error=dev
        deprecated : bool?      # -Werror=deprecated or -Wno-error=deprecated

    type DebugObject:
        output : bool?          # --debug-output if true
        tryCompile : bool?      # --debug-trycompile  if true
        find : bool?            # --debug-find

    type Toolset:
        value : string?
        strategy : "set|external"?
