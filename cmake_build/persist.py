# -*- coding: UTF-8 -*-
"""
This module contains utility class to load and store persistent data.
"""

from __future__ import absolute_import
import json
from codecs import open     # pylint: disable=redefined-builtin
from path import Path


class Unknown(object):
    pass


class PersistentData(object):
    """Provides the core functionality for persistent data as abstract base class.

    .. code-block::

        from cmake_build.persist import PersistentData
        class FooData(PersistentData):
            FILE_BASENAME = "foo.config.json"


        foo_data1 = FooData.load()
        foo_data2 = FooData.load("path/to/foo.config.json")

        foo_data1.save()
        foo_data2.save("more/foo.config.json")
    """
    FILE_BASENAME = "persistent.json"

    def __init__(self, filename=None, data=None, **kwargs):
        self.filename = Path(filename or self.FILE_BASENAME)
        self.data = data or {}
        self.data.update(**kwargs)

    def make_data(self):
        return self.data

    # -- DICT-LIKE:
    # def copy(self):
    #     return self.__class__(self.filename, data=self.make_data().copy())
    #
    # def get(self, name, default=None):
    #     value = getattr(self, name, Unknown)
    #     if value is Unknown:
    #         value = self.data.get(name, default)
    #     return value
    #
    def clear(self):
        # -- KEEP: self.data_dir
        self.data = {}

    def assign(self, data):
        # -- WORKS WITH: this-class or dict-like
        the_data = data
        if isinstance(data, self.__class__):
            the_data = data.data
        self.data = the_data.copy()

    # -- PATH-LIKE:
    def exists(self):
        """Checks if persistent data file exists."""
        assert not self.filename.exists() or self.filename.isfile()
        return self.filename.exists()

    def remove(self):
        """Remove persistent data file (if it exists)."""
        self.filename.remove_p()

    # -- LOADING/STORING, ...
    def dump(self, readable=True):
        """Dumps data as text."""
        data = self.make_data()
        extra_args = {}
        if readable:
            extra_args = dict(sort_keys=True, indent=4)
        return json.dumps(data, **extra_args)

    def save(self, filename=None):
        filename = Path(filename or self.filename)
        dirname = filename.dirname()
        dirname.makedirs_p()    # pylint: disable=no-value-for-parameter
        with open(filename, "wb", encoding="UTF-8") as f:
            text_data = self.dump()
            f.write(text_data)
            f.write("\n")
        return self

    @classmethod
    def parse(cls, text, encoding=None):
        encoding = encoding or "UTF-8"
        data = json.loads(text, encoding=encoding)
        return data

    @classmethod
    def load(cls, filename):
        filename = Path(filename)
        persistent_object = cls(filename)
        if not filename.exists():
            return persistent_object

        with open(filename, "r", encoding="UTF-8") as f:
            text = f.read()
            data = cls.parse(text)
            persistent_object.clear()
            persistent_object.assign(data)
        return persistent_object
