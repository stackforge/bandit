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

import ast
import re

import bandit
from bandit.core import test_properties as test


def _has_special_characters(command):
    # check if it contains any of the characters that may cause globing,
    # multiple commands, subshell, or variable resolution
    # glob: [ { * ?
    # variable: $
    # subshell: ` $
    return bool(re.search(r'[{|\[;$\*\?`]', command))


def _evaluate_shell_call(context):
    no_formatting = isinstance(context.node.args[0], ast.Str)
    if no_formatting:
        command = context.call_args[0]
        no_special_chars = not _has_special_characters(command)
    else:
        no_special_chars = False

    if no_formatting and no_special_chars:
        return bandit.LOW
    elif no_formatting:
        return bandit.MEDIUM
    else:
        return bandit.HIGH


@test.takes_config('shell_injection')
@test.checks('Call')
@test.test_id('B502')
def subprocess_popen_with_shell_equals_true(context, config):
    """subprocess_popen_with_shell_equals_true

    Python possesses many mechanisms to invoke an external executable. However,
    doing so may present a security issue if appropriate care is not taken to
    sanitize any user provided or variable input.

    This plugin test is part of a family of tests built to check for process
    spawning and warn appropriately. Specifically, this test looks for the
    spawning of a subprocess using a command shell. This type of subprocess
    invocation is dangerous as it is vulnerable to various shell injection
    attacks. Great care should be taken to sanitize all input in order to
    mitigate this risk. Calls of this type are identified by a parameter of
    "shell=True" being given.

    Additionally, this plugin scans the command string given and adjusts its
    reported severity based on how it is presented. If the command string is a
    simple static string containing no special shell characters, then the
    resulting issue has low severity. If the string is static, but contains
    shell formatting characters or wildcards, then the reported issue is
    medium. Finally, if the string is computed using Python's string
    manipulation or formatting operations, then the reported issue has high
    severity. These severity levels reflect the likelihood that the code is
    vulnerable to injection.

    See also:

    - :doc:`../plugins/linux_commands_wildcard_injection`
    - :doc:`../plugins/subprocess_without_shell_equals_true`
    - :doc:`../plugins/start_process_with_no_shell`
    - :doc:`../plugins/start_process_with_a_shell`
    - :doc:`../plugins/start_process_with_partial_path`

    Config Options:

    This plugin test shares a configuration with others in the same family,
    namely `shell_injection`. This configuration is divided up into three
    sections, `subprocess`, `shell` and `no_shell`. They each list Python calls
    that spawn subprocesses, invoke commands within a shell, or invoke commands
    without a shell (by replacing the calling process) respectively.

    This plugin specifically scans for methods listed in `subprocess` section
    that have shell=True specified.

    .. code-block:: yaml

        shell_injection:

            # Start a process using the subprocess module, or one of its
            wrappers.
            subprocess:
                - subprocess.Popen
                - subprocess.call


    Sample Output:

    .. code-block:: none

        >> Issue: subprocess call with shell=True seems safe, but may be
        changed in the future, consider rewriting without shell
           Severity: Low   Confidence: High
           Location: ./examples/subprocess_shell.py:21
        20  subprocess.check_call(['/bin/ls', '-l'], shell=False)
        21  subprocess.check_call('/bin/ls -l', shell=True)
        22

        >> Issue: call with shell=True contains special shell characters,
        consider moving extra logic into Python code
           Severity: Medium   Confidence: High
           Location: ./examples/subprocess_shell.py:26
        25
        26  subprocess.Popen('/bin/ls *', shell=True)
        27  subprocess.Popen('/bin/ls %s' % ('something',), shell=True)

        >> Issue: subprocess call with shell=True identified, security issue.
           Severity: High   Confidence: High
           Location: ./examples/subprocess_shell.py:27
        26  subprocess.Popen('/bin/ls *', shell=True)
        27  subprocess.Popen('/bin/ls %s' % ('something',), shell=True)
        28  subprocess.Popen('/bin/ls {}'.format('something'), shell=True)

    References:

    - https://security.openstack.org
    - https://docs.python.org/2/library/subprocess.html#frequently-used-arguments  # noqa
    - https://security.openstack.org/guidelines/dg_use-subprocess-securely.html
    - https://security.openstack.org/guidelines/dg_avoid-shell-true.html

    .. versionadded:: 0.9.0
    """
    if config and context.call_function_name_qual in config['subprocess']:
        if context.check_call_arg_value('shell', 'True'):
            if len(context.call_args) > 0:
                sev = _evaluate_shell_call(context)
                if sev == bandit.LOW:
                    return bandit.Issue(
                        severity=bandit.LOW,
                        confidence=bandit.HIGH,
                        text="subprocess call with shell=True seems safe, but "
                             "may be changed in the future, consider "
                             "rewriting without shell"
                    )
                elif sev == bandit.MEDIUM:
                    return bandit.Issue(
                        severity=bandit.MEDIUM,
                        confidence=bandit.HIGH,
                        text="call with shell=True contains special shell "
                             "characters, consider moving extra logic into "
                             "Python code"
                    )
                else:
                    return bandit.Issue(
                        severity=bandit.HIGH,
                        confidence=bandit.HIGH,
                        text="subprocess call with shell=True identified, "
                             "security issue."
                    )


@test.takes_config('shell_injection')
@test.checks('Call')
@test.test_id('B503')
def subprocess_without_shell_equals_true(context, config):
    """subprocess_without_shell_equals_true

    Python possesses many mechanisms to invoke an external executable. However,
    doing so may present a security issue if appropriate care is not taken to
    sanitize any user provided or variable input.

    This plugin test is part of a family of tests built to check for process
    spawning and warn appropriately. Specifically, this test looks for the
    spawning of a subprocess without the use of a command shell. This type of
    subprocess invocation is not vulnerable to shell injection attacks, but
    care should still be taken to ensure validity of input.

    Because this is a lesser issue than that described in
    `subprocess_popen_with_shell_equals_true` a LOW severity warning is
    reported.

    See also:

    - :doc:`../plugins/linux_commands_wildcard_injection`
    - :doc:`../plugins/subprocess_popen_with_shell_equals_true`
    - :doc:`../plugins/start_process_with_no_shell`
    - :doc:`../plugins/start_process_with_a_shell`
    - :doc:`../plugins/start_process_with_partial_path`

    Config Options:

    This plugin test shares a configuration with others in the same family,
    namely `shell_injection`. This configuration is divided up into three
    sections, `subprocess`, `shell` and `no_shell`. They each list Python calls
    that spawn subprocesses, invoke commands within a shell, or invoke commands
    without a shell (by replacing the calling process) respectively.

    This plugin specifically scans for methods listed in `subprocess` section
    that have shell=False specified.

    .. code-block:: yaml

        shell_injection:
            # Start a process using the subprocess module, or one of its
            wrappers.
            subprocess:
                - subprocess.Popen
                - subprocess.call


    Sample Output:

    .. code-block:: none

        >> Issue: subprocess call - check for execution of untrusted input.
           Severity: Low   Confidence: High
           Location: ./examples/subprocess_shell.py:23
        22
        23    subprocess.check_output(['/bin/ls', '-l'])
        24

    References:

    - https://security.openstack.org
    - https://docs.python.org/2/library/subprocess.html#frequently-used-arguments  # noqa
    - https://security.openstack.org/guidelines/dg_avoid-shell-true.html
    - https://security.openstack.org/guidelines/dg_use-subprocess-securely.html

    .. versionadded:: 0.9.0
    """
    if config and context.call_function_name_qual in config['subprocess']:
        if not context.check_call_arg_value('shell', 'True'):
            return bandit.Issue(
                severity=bandit.LOW,
                confidence=bandit.HIGH,
                text="subprocess call - check for execution of untrusted "
                     "input."
            )


@test.takes_config('shell_injection')
@test.checks('Call')
@test.test_id('B504')
def any_other_function_with_shell_equals_true(context, config):
    """any_other_function_with_shell_equals_true

    Python possesses many mechanisms to invoke an external executable. However,
    doing so may present a security issue if appropriate care is not taken to
    sanitize any user provided or variable input.

    This plugin test is part of a family of tests built to check for process
    spawning and warn appropriately. Specifically, this plugin test
    interrogates method calls for the presence of a keyword parameter `shell`
    equalling true. It is related to detection of shell injection issues and is
    intended to catch custom wrappers to vulnerable methods that may have been
    created.

    See also:

    - :doc:`../plugins/linux_commands_wildcard_injection`
    - :doc:`../plugins/subprocess_popen_with_shell_equals_true`
    - :doc:`../plugins/subprocess_without_shell_equals_true`
    - :doc:`../plugins/start_process_with_no_shell`
    - :doc:`../plugins/start_process_with_a_shell`
    - :doc:`../plugins/start_process_with_partial_path`

    Config Options:

    This plugin test shares a configuration with others in the same family,
    namely `shell_injection`. This configuration is divided up into three
    sections, `subprocess`, `shell` and `no_shell`. They each list Python calls
    that spawn subprocesses, invoke commands within a shell, or invoke commands
    without a shell (by replacing the calling process) respectively.

    Specifically, this plugin excludes those functions listed under the
    subprocess section, these methods are tested in a separate specific test
    plugin and this exclusion prevents duplicate issue reporting.

    .. code-block:: yaml

        shell_injection:
            # Start a process using the subprocess module, or one of its
            wrappers.
            subprocess: [subprocess.Popen, subprocess.call,
                         subprocess.check_call, subprocess.check_output,
                         utils.execute, utils.execute_with_timeout]


    Sample Output:

    .. code-block:: none

        >> Issue: Function call with shell=True parameter identified, possible
        security issue.
           Severity: Medium   Confidence: High
           Location: ./examples/subprocess_shell.py:9
        8 pop('/bin/gcc --version', shell=True)
        9 Popen('/bin/gcc --version', shell=True)
        10

    References:

     - https://security.openstack.org/guidelines/dg_avoid-shell-true.html
     - https://security.openstack.org/guidelines/dg_use-subprocess-securely.html  # noqa
    """
    '''Alerts on any function call that includes a shell=True parameter.

    Multiple "helpers" with varying names have been identified across
    various OpenStack projects.

    .. versionadded:: 0.9.0
    '''
    if config and context.call_function_name_qual not in config['subprocess']:
        if context.check_call_arg_value('shell', 'True'):
            return bandit.Issue(
                severity=bandit.MEDIUM,
                confidence=bandit.LOW,
                text="Function call with shell=True parameter identifed, "
                     "possible security issue."
                )


@test.takes_config('shell_injection')
@test.checks('Call')
@test.test_id('B505')
def start_process_with_a_shell(context, config):
    """start_process_with_a_shell

    Python possesses many mechanisms to invoke an external executable. However,
    doing so may present a security issue if appropriate care is not taken to
    sanitize any user provided or variable input.

    This plugin test is part of a family of tests built to check for process
    spawning and warn appropriately. Specifically, this test looks for the
    spawning of a subprocess using a command shell. This type of subprocess
    invocation is dangerous as it is vulnerable to various shell injection
    attacks. Great care should be taken to sanitize all input in order to
    mitigate this risk. Calls of this type are identified by the use of certain
    commands which are known to use shells. Bandit will report a MEDIUM
    severity warning.

    See also:

    - :doc:`../plugins/linux_commands_wildcard_injection`
    - :doc:`../plugins/subprocess_without_shell_equals_true`
    - :doc:`../plugins/start_process_with_no_shell`
    - :doc:`../plugins/start_process_with_partial_path`
    - :doc:`../plugins/subprocess_popen_with_shell_equals_true`

    Config Options:

    This plugin test shares a configuration with others in the same family,
    namely `shell_injection`. This configuration is divided up into three
    sections, `subprocess`, `shell` and `no_shell`. They each list Python calls
    that spawn subprocesses, invoke commands within a shell, or invoke commands
    without a shell (by replacing the calling process) respectively.

    This plugin specifically scans for methods listed in `shell` section.

    .. code-block:: yaml

        shell_injection:
            shell:
                - os.system
                - os.popen
                - os.popen2
                - os.popen3
                - os.popen4
                - popen2.popen2
                - popen2.popen3
                - popen2.popen4
                - popen2.Popen3
                - popen2.Popen4
                - commands.getoutput
                - commands.getstatusoutput

    Sample Output:

    .. code-block:: none

        >> Issue: Starting a process with a shell: check for injection.
           Severity: Medium   Confidence: Medium
           Location: examples/os_system.py:3
        2
        3   os.system('/bin/echo hi')

    References:

    - https://security.openstack.org
    - https://docs.python.org/2/library/os.html#os.system
    - https://docs.python.org/2/library/subprocess.html#frequently-used-arguments  # noqa
    - https://security.openstack.org/guidelines/dg_use-subprocess-securely.html

    .. versionadded:: 0.10.0
    """
    if config and context.call_function_name_qual in config['shell']:
        if len(context.call_args) > 0:
            sev = _evaluate_shell_call(context)
            if sev == bandit.LOW:
                return bandit.Issue(
                    severity=bandit.LOW,
                    confidence=bandit.HIGH,
                    text="Starting a process with a shell: "
                         "Seems safe, but may be changed in the future, "
                         "consider rewriting without shell"
                )
            elif sev == bandit.MEDIUM:
                return bandit.Issue(
                    severity=bandit.MEDIUM,
                    confidence=bandit.HIGH,
                    text="Starting a process with a shell and special shell "
                         "characters, consider moving extra logic into "
                         "Python code"
                )
            else:
                return bandit.Issue(
                    severity=bandit.HIGH,
                    confidence=bandit.HIGH,
                    text="Starting a process with a shell, possible injection"
                         " detected, security issue."
                )


@test.takes_config('shell_injection')
@test.checks('Call')
@test.test_id('B506')
def start_process_with_no_shell(context, config):
    """start_process_with_no_shell

    Python possesses many mechanisms to invoke an external executable. However,
    doing so may present a security issue if appropriate care is not taken to
    sanitize any user provided or variable input.

    This plugin test is part of a family of tests built to check for process
    spawning and warn appropriately. Specifically, this test looks for the
    spawning of a subprocess in a way that doesn't use a shell. Although this
    is generally safe, it maybe useful for penetration testing workflows to
    track where external system calls are used.  As such a LOW severity message
    is generated.

    See also:

    - :doc:`../plugins/linux_commands_wildcard_injection`
    - :doc:`../plugins/subprocess_without_shell_equals_true`
    - :doc:`../plugins/start_process_with_a_shell`
    - :doc:`../plugins/start_process_with_partial_path`
    - :doc:`../plugins/subprocess_popen_with_shell_equals_true`

    Config Options:

    This plugin test shares a configuration with others in the same family,
    namely `shell_injection`. This configuration is divided up into three
    sections, `subprocess`, `shell` and `no_shell`. They each list Python calls
    that spawn subprocesses, invoke commands within a shell, or invoke commands
    without a shell (by replacing the calling process) respectively.

    This plugin specifically scans for methods listed in `no_shell` section.

    .. code-block:: yaml

        shell_injection:
            no_shell:
                - os.execl
                - os.execle
                - os.execlp
                - os.execlpe
                - os.execv
                - os.execve
                - os.execvp
                - os.execvpe
                - os.spawnl
                - os.spawnle
                - os.spawnlp
                - os.spawnlpe
                - os.spawnv
                - os.spawnve
                - os.spawnvp
                - os.spawnvpe
                - os.startfile

    Sample Output:

    .. code-block:: none

        >> Issue: [start_process_with_no_shell] Starting a process without a
           shell.
           Severity: Low   Confidence: Medium
           Location: examples/os-spawn.py:8
        7   os.spawnv(mode, path, args)
        8   os.spawnve(mode, path, args, env)
        9   os.spawnvp(mode, file, args)

    References:

    - https://security.openstack.org
    - https://docs.python.org/2/library/os.html#os.system
    - https://docs.python.org/2/library/subprocess.html#frequently-used-arguments  # noqa
    - https://security.openstack.org/guidelines/dg_use-subprocess-securely.html

    .. versionadded:: 0.10.0
    """

    if config and context.call_function_name_qual in config['no_shell']:
        return bandit.Issue(
            severity=bandit.LOW,
            confidence=bandit.MEDIUM,
            text="Starting a process without a shell."
        )


@test.takes_config('shell_injection')
@test.checks('Call')
@test.test_id('B507')
def start_process_with_partial_path(context, config):
    """start_process_with_partial_path

    Python possesses many mechanisms to invoke an external executable. If the
    desired executable path is not fully qualified relative to the filesystem
    root then this may present a potential security risk.

    In POSIX environments, the `PATH` environment variable is used to specify a
    set of standard locations that will be searched for the first matching
    named executable. While convenient, this behavior may allow a malicious
    actor to exert control over a system. If they are able to adjust the
    contents of the `PATH` variable, or manipulate the file system, then a
    bogus executable may be discovered in place of the desired one. This
    executable will be invoked with the user privileges of the Python process
    that spawned it, potentially a highly privileged user.

    This test will scan the parameters of all configured Python methods,
    looking for paths that do not start at the filesystem root, that is, do not
    have a leading '/' character.

    Config Options:

    This plugin test shares a configuration with others in the same family,
    namely `shell_injection`. This configuration is divided up into three
    sections, `subprocess`, `shell` and `no_shell`. They each list Python calls
    that spawn subprocesses, invoke commands within a shell, or invoke commands
    without a shell (by replacing the calling process) respectively.

    This test will scan parameters of all methods in all sections. Note that
    methods are fully qualified and de-aliased prior to checking.

    .. code-block:: yaml

        shell_injection:
            # Start a process using the subprocess module, or one of its
            wrappers.
            subprocess:
                - subprocess.Popen
                - subprocess.call

            # Start a process with a function vulnerable to shell injection.
            shell:
                - os.system
                - os.popen
                - popen2.Popen3
                - popen2.Popen4
                - commands.getoutput
                - commands.getstatusoutput
            # Start a process with a function that is not vulnerable to shell
            injection.
            no_shell:
                - os.execl
                - os.execle


    Sample Output:

    .. code-block:: none

        >> Issue: Starting a process with a partial executable path
        Severity: Low   Confidence: High
        Location: ./examples/partial_path_process.py:3
        2    from subprocess import Popen as pop
        3    pop('gcc --version', shell=False)

    References:

    - https://security.openstack.org
    - https://docs.python.org/2/library/os.html#process-management

    .. versionadded:: 0.13.0
    """

    if config and len(context.call_args):
        if(context.call_function_name_qual in config['subprocess'] or
           context.call_function_name_qual in config['shell'] or
           context.call_function_name_qual in config['no_shell']):

            delims = ['/', '\\', '.']
            node = context.node.args[0]
            # some calls take an arg list, check the first part
            if isinstance(node, ast.List):
                node = node.elts[0]

            # make sure the param is a string literal and not a var name
            if(isinstance(node, ast.Str) and node.s[0] not in delims):
                return bandit.Issue(
                    severity=bandit.LOW,
                    confidence=bandit.HIGH,
                    text="Starting a process with a partial executable path"
                )
