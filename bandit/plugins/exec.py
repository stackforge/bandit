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

r"""
Description
-----------
This plugin test checks for the use of Python's `exec` method or keyword. The
Python docs succinctly describe why the use of `exec` is risky:

 - `This statement supports dynamic execution of Python code.` [1]_

Available Since
---------------
 - Bandit v0.9.0

Config Options
--------------
None

Sample Output
-------------
.. code-block:: none

    >> Issue: Use of exec detected.
       Severity: Medium   Confidence: High
       Location: ./examples/exec-py2.py:2
    1 exec("do evil")
    2 exec "do evil"

References
----------
.. [1] https://docs.python.org/2.0/ref/exec.html
.. [2] TODO : add info on exec and similar to sec best practice and link here

"""

import six

import bandit
from bandit.core.test_properties import *


def exec_issue():
    return bandit.Issue(
        severity=bandit.MEDIUM,
        confidence=bandit.HIGH,
        text="Use of exec detected."
    )


if six.PY2:
    @checks('Exec')
    def exec_used(context):
        return exec_issue()
else:
    @checks('Call')
    def exec_used(context):
        if context.call_function_name_qual == 'exec':
            return exec_issue()
