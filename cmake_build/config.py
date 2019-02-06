# STATUS: PREPARED (for click support)
# pylint: disable=unused-argument, no-self-use

# ---------------------------------------------------------------------------
# PREPARED:
# ---------------------------------------------------------------------------
CMAKE_BUILD_TARGETS = [
    "init", "build", "test", "clean", "reinit", "rebuild"
    # MAYBE: install, cpack, ctest
]


class CMakeBuildConfig(object):
    DEFAULT_FILENAME = "cmake-build.config.yaml"
    DEFAULT_TARGET = "build"
    CONFIG_DEFAULTS = {
        "generator": None,
        "toolchain": None,
        "build_config": "debug",
        "build_configs": dict(debug={}, release={}),
        "projects": [],
        # DISABLED: "build_config_aliases": dict(default="default"),
    }

    def __init__(self, filename=None, **kwargs):
        self.filename = filename or self.DEFAULT_FILENAME
        self.build_config = None
        self.project = None
        self.target = self.DEFAULT_TARGET
        for name, value in kwargs.items():
            setattr(self, name, value)
        self.data = {}
        self.data.update(self.CONFIG_DEFAULTS)

    def load(self, filename=None):
        # PREPARED:
        filename = filename or self.filename


class CMakeBuildConfigValidator(object):

    def __init__(self, config):
        self.config = config
        self.error_message = None

    @property
    def build_config(self):
        return self.config.get("build_config", "debug")

    def check_build_config(self, build_config=None):
        build_config = build_config or self.build_config
        okay = build_config in self.config["build_configs"]
        if not okay:
            self.error_message = "BAD-BUILD-CONFIG={0}".format(build_config)

    def check_project(self, project):
        return NotImplemented

    def check(self, config=None):
        config = config or self.config
        assert config is not None
        if self.check_build_config(config.build_config):
            return False
        return True
