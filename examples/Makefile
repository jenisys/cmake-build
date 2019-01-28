# ===========================================================================
# MAKEFILE: cmake-build/examples/
# ===========================================================================
# MAKE-DIALECT: GNU Make (due to GNU Make functions: define .. endef)
# DESCRIPTION:
#   Intermediate build script until cmake-build is working properly.
#
# GOAL:
#    Ensure that CMake files/tasks are working properly
#
# USAGE:
#   make
#   make BUILD_CONFIG=Debug
#   make BUILD_CONFIG=Release
#   make all-build_config
#   make clean
#
# ===========================================================================


# ---------------------------------------------------------------------------
# MAKE DEFINITIONS:
# ---------------------------------------------------------------------------
CMAKE_GENERATOR := Ninja
BUILD_CONFIG ?= Debug


# ---------------------------------------------------------------------------
# MAKE FUNCTIONS:
# ---------------------------------------------------------------------------
define cmake_init
  mkdir -p $(1) && cd $(1) && cmake -G $(CMAKE_GENERATOR) ..
endef
define cmake_ensure_init
  test -d $(1) || ( $(call cmake_init,$(1)) )
endef
define cmake_build
  cd $(1) && cmake --build .
endef


# ---------------------------------------------------------------------------
# MAKE RULES:
# ---------------------------------------------------------------------------
.PHONY: all all-build_config clean
.FORCE: ;
# .PHONY: cmake_program_hello/build.Debug cmake_program_hello/build.Release
# .PHONY: cmake_library_hello/build.Debug cmake_library_hello/build.Release

all: cmake__library_hello/build.$(BUILD_CONFIG)
all: cmake__program_hello/build.$(BUILD_CONFIG)

all-build_config:
	@echo "CMAKE-BUILD: $(@)"
	$(MAKE) BUILD_CONFIG=Debug
	$(MAKE) BUILD_CONFIG=Release


# -- CMAKE ANY-TARGETS:
_CMAKE_PROJECT_BUILD_DIR = $(subst cmake__,,$(@))
cmake__program_hello/build.%: .FORCE
	@echo "CMAKE-BUILD: BUILD_DIR=$(_CMAKE_PROJECT_BUILD_DIR)"
	$(call cmake_ensure_init,$(_CMAKE_PROJECT_BUILD_DIR))
	$(call cmake_build,$(_CMAKE_PROJECT_BUILD_DIR))

cmake__library_hello/build.%: .FORCE
	@echo "CMAKE-BUILD: BUILD_DIR=$(_CMAKE_PROJECT_BUILD_DIR)"
	$(call cmake_ensure_init,$(_CMAKE_PROJECT_BUILD_DIR))
	$(call cmake_build,$(_CMAKE_PROJECT_BUILD_DIR))


# -- CLEANUP:
clean:
	@echo "$(@): Cleanup everything ..."
	-rm -rf program_hello/build.*
	-rm -rf library_hello/build.*
