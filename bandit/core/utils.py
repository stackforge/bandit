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

import _ast
import ast
import logging
import os.path
import symtable
import sys


"""Various helper functions."""


def ast_args_to_str(args):
        res = ('\n\tArgument/s:\n\t\t%s' %
               '\n\t\t'.join([ast.dump(arg) for arg in args]))
        return res


def get_call_name(node, aliases):
    if type(node.func) == _ast.Name:
        if deepgetattr(node, 'func.id') in aliases:
            return aliases[deepgetattr(node, 'func.id')]
        return(deepgetattr(node, 'func.id'))
    elif type(node.func) == _ast.Attribute:
        prefix = ""
        if type(node.func.value) == _ast.Name:
            if deepgetattr(node, 'func.value.id') in aliases:
                prefix = aliases[deepgetattr(node, 'func.value.id')] + "."
            else:
                prefix = deepgetattr(node, 'func.value.id') + "."
        return("%s%s" % (prefix, deepgetattr(node, 'func.attr')))
    else:
        return ""


def get_func_name(node):
    return node.name  # TODO(tkelsey): get that qualname using enclosing scope


def get_qual_attr(node, aliases):
    prefix = ""
    if type(node) == _ast.Attribute:
        try:
            val = deepgetattr(node, 'value.id')
            if val in aliases:
                prefix = aliases[val]
            else:
                prefix = deepgetattr(node, 'value.id')
        except Exception:
            # NOTE(tkelsey): degrade gracefully when we cant get the fully
            # qualified name for an attr, just return its base name.
            pass

        return("%s.%s" % (prefix, node.attr))
    else:
        return ""  # TODO(tkelsey): process other node types


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    for key in attr.split('.'):
        obj = getattr(obj, key)
    return obj


def describe_symbol(sym):
    assert type(sym) == symtable.Symbol
    print("Symbol:", sym.get_name())

    for prop in [
            'referenced', 'imported', 'parameter',
            'global', 'declared_global', 'local',
            'free', 'assigned', 'namespace']:
        if getattr(sym, 'is_' + prop)():
            print('    is', prop)


def mid_range(mid, count):
    if count == 1:
        return range(mid, mid + 1)
    diff = count / 2
    if count % 2 == 0:
        start = mid - diff
        stop = mid + diff
    else:
        start = mid - diff
        stop = mid + diff + 1
    if start < 1:
        stop = stop + (start * -1) + 1
        start = 1
    return range(start, stop)


class InvalidModulePath(Exception):
    pass


def get_module_qualname_from_path(path):
    '''Get the module's qualified name by analysis of the path.

    Resolve the absolute pathname and eliminate symlinks. This could result in
    an incorrect name if symlinks are used to restructure the python lib
    directory.

    Starting from the right-most directory component look for __init__.py in
    the directory component. If it exists then the directory name is part of
    the module name. Move left to the subsequent directory components until a
    directory is found without __init__.py.

    :param: Path to module file. Relative paths will be resolved relative to
            current working directory.
    :return: fully qualified module name
    '''

    abspath = os.path.abspath(path)
    (head, tail) = os.path.split(path)
    if head == '' or tail == '':
        raise InvalidModulePath('Invalid python file path: "{}"'
                                ' Missing path or file name'.format(path))

    found_syspath = False
    for syspath in sys.path:
        if abspath.startswith(os.path.abspath(syspath)):
            found_syspath = True
            break
    if not found_syspath:
        log = logging.getLogger()
        log.warn('Module (%s) is not installed in python sys.path. '
                 'Names defined in this module may not be fully qualified.',
                 path)

    qname = [os.path.splitext(tail)[0]]
    while head != '/':
        if os.path.isfile(os.path.join(head, '__init__.py')):
            (head, tail) = os.path.split(head)
            qname.insert(0, tail)
        else:
            break

    qualname = '.'.join(qname)
    return qualname


def namespace_path_join(base, name):
    '''Extend the current namespace path with an additional name

    Take a namespace path (i.e., package.module.class) and extends it
    with an additional name (i.e., package.module.class.subclass).
    This is similar to how os.path.join works.

    :param base: (String) The base namespace path.
    :param name: (String) The new name to append to the base path.
    :returns: (String) A new namespace path resulting from combination of
              base and name.
    '''
    return '{}.{}'.format(base, name)


def namespace_path_split(path):
    '''Split the namespace path into a pair (head, tail).

    Tail will be the last namespace path component and head will
    be everything leading up to that in the path. This is similar to
    os.path.split.

    :param path: (String) A namespace path.
    :returns: (String, String) A tuple where the first component is the base
              path and the second is the last path component.
    '''
    return tuple(path.rsplit('.', 1))
