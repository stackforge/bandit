# -*- coding:utf-8 -*-
#
# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import importlib
import logging

import six

from bandit.core import blacklisting
from bandit.core import extension_loader


logger = logging.getLogger(__name__)

# These IDs are for bandit built in tests
builtins = ['B001']


class BanditTestSet():
    def __init__(self, config, profile={}):
        extman = extension_loader.MANAGER
        filtering = self._get_filter(profile)
        self.plugins = [p for p in extman.plugins
                        if p.plugin._test_id in filtering]
        self.plugins.extend(self._load_builtins(filtering, config))
        self._load_tests(config, self.plugins)

    def _get_filter(self, profile):
        extman = extension_loader.MANAGER

        def _get_id(value):
            # Here we normalize on plugin IDs, by converting any names.
            # If we cant convert it then we just return it, this is OK.
            return extman.get_plugin_id(value) or value

        inc = set(_get_id(i) for i in (profile.get('include') or []))
        exc = set(_get_id(e) for e in (profile.get('exclude') or []))
        filtered = inc or list(extman.plugins_by_id.keys())

        # blacklist data and builtins
        if not inc:
            filtered.extend(builtins)
            for node, tests in six.iteritems(extman.blacklist):
                filtered.extend([t['id'] for t in tests])

        return set(f for f in filtered if f not in exc)

    def _load_builtins(self, filtering, config):
        '''loads up out builtin functions, so they can be filtered.'''
        class Wrapper:
            def __init__(self, name, plugin):
                self.name = name
                self.plugin = plugin

        results = []

        if 'B001' in filtering:
            extman = extension_loader.MANAGER
            blacklist = self._config_compat(config)
            if not blacklist:  # this is overridden by config, so skip
                for node, tests in six.iteritems(extman.blacklist):
                    values = [t for t in tests if t['id'] in filtering]
                    if values:
                        blacklist[node] = values

            # this dresses up the blacklist to look like a plugin, but the
            # '_checks' data comes from the blacklist information.
            # '_config' is the filtered blacklist data set.
            setattr(blacklisting.blacklist, "_test_id", 'B001')
            setattr(blacklisting.blacklist, "_checks", blacklist.keys())
            setattr(blacklisting.blacklist, "_config", blacklist)
            results.append(Wrapper('blacklist', blacklisting.blacklist))

        return results

    def _load_tests(self, config, plugins):
        '''Builds a dict mapping tests to node types.'''
        self.tests = {}
        for plugin in plugins:
            if hasattr(plugin.plugin, '_takes_config'):
                # TODO(??): config could come from profile ...
                cfg = config.get_option(plugin.plugin._takes_config)
                if cfg is None:
                    genner = importlib.import_module(plugin.plugin.__module__)
                    cfg = genner.gen_config(plugin.plugin._takes_config)
                plugin.plugin._config = cfg
            for check in plugin.plugin._checks:
                self.tests.setdefault(check, []).append(plugin.plugin)
                logger.debug('added function %s (%s) targetting %s',
                             plugin.name, plugin.plugin._test_id, check)

    def _config_compat(self, config):
        '''This reads the old blacklist config and builds compatible data.'''
        blacklist = {}
        bl_calls = config.get_setting('blacklist_calls')
        bl_imports = config.get_setting('blacklist_imports')

        if bl_imports:
            bl_imports = bl_imports['bad_import_sets']
            for item in bl_imports:  # patch up the message format
                item['message'] = item['message'].replace('{module}', '{name}')
            blacklist.setdefault('Import', []).extend(bl_imports)
            blacklist.setdefault('ImportFrom', []).extend(bl_imports)
            blacklist.setdefault('Call', []).extend(bl_imports)

        if bl_calls:
            bl_calls = bl_calls['bad_name_sets']
            for item in bl_calls:  # patch up the message format
                item['message'] = item['message'].replace('{func}', '{name}')
            blacklist.setdefault('Call', []).extend(bl_calls)
        return blacklist

    def get_tests(self, checktype):
        '''Returns all tests that are of type checktype

        :param checktype: The type of test to filter on
        :return: A list of tests which are of the specified type
        '''
        return self.tests.get(checktype) or []
