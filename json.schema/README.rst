JSON SCHEMA
===============================================================================

Contains JSON schemas:

* CMakePresets.schema.json

RELATED TO: CMakePresets

* https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html
* https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html#schema


EXAMPLE:
-------------------------------------------------------------------------------

.. code:: bash

    # -- REQUIRES: pip install check-jsonschema
    check-jsonschema --schemafile=CMakePresets.schema.json CMakePresets.json
