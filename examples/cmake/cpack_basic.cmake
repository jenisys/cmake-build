# ===========================================================================
# CPACK: Basic Definitions for a CMake Project
# ===========================================================================
# BLUEPRINT: https://github.com/serge-sans-paille/frozen.git

# MAYBE: if(NOT subproject)
set(CPACK_PACKAGE_NAME "${PROJECT_NAME}")
# XXX set(CPACK_PACKAGE_VENDOR "__UNDEFINED_")
# MAYBE: set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
# OR: set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_VERSION_MAJOR "${PROJECT_VERSION_MAJOR}")
set(CPACK_PACKAGE_VERSION_MINOR "${PROJECT_VERSION_MINOR}")
set(CPACK_PACKAGE_VERSION_PATCH "${PROJECT_VERSION_PATCH}")
# XXX set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "a C++14 header-only, constexpr alternative to gperf")
# XXX set(CMAKE_PROJECT_HOMEPAGE_URL "https://blog.quarkslab.com/frozen-an-header-only-constexpr-alternative-to-gperf-for-c14-users.html")
# set(CPACK_IGNORE_FILES "\\.psd$;/CVS/;/\\.svn/;/\\.git/;\\.swp$;/CMakeLists.txt.user;\\.#;/#;\\.tar.gz$;/CMakeFiles/;CMakeCache.txt;\\.qm$;/build/;\\.diff$;.DS_Store'")
set(CPACK_SOURCE_GENERATOR "ZIP")
# set(CPACK_SOURCE_PACKAGE_FILE_NAME "${CPACK_PACKAGE_NAME}-${CPACK_PACKAGE_VERSION}")
set(CPACK_SOURCE_IGNORE_FILES ${CPACK_IGNORE_FILES})

# CPACK_PACKAGE_DESCRIPTION_FILE
# CPACK_PACKAGE_DESCRIPTION_SUMMARY
# CPACK_PACKAGE_FILE_NAME
# CPACK_PACKAGE_CONTACT
# CPACK_SOURCE_GENERATOR
# CPACK_SYSTEM_NAME

# -- ADVANCED:
# CPACK_RESOURCE_FILE_LICENSE
# CPACK_RESOURCE_FILE_README
# CPACK_PACKAGE_VERSION
# CPACK_OUTPUT_FILE_PREFIX

include(CPack)

