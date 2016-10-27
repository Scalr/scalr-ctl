__author__ = 'Dmitriy Korsakov'

import pytest

import os
import subprocess


class Runner:

    long_prefix = '--'
    long_jumper = None

    def _prepare_args(self, *args, **long_args):
        _args = []
        for arg in args:
            _args.append(str(arg))
        for name, value in list(long_args.items()):
            name = name.replace('_', '-')
            if self.long_prefix:
                name = '{0}{1}'.format(self.long_prefix, name)
            if self.long_jumper:
                if type(value) == bool and value:
                    _args.append(name)
                else:
                    _args.append(''.join([name, self.long_jumper, str(value)]))
            else:
                _args.append(name)
                if type(value) == bool and value:
                    continue
                _args.append(str(value))
        return _args

    def which(self, program):
        if program and program.startswith('/') and os.access(program, os.X_OK):
            return program
        for where in set(os.environ['PATH'].split(os.pathsep)):
            path = os.path.join(where, program)
            if os.access(path, os.X_OK):
                return path

    @property
    def bin_path(self):
        return self.which("scalr-ctl")

    def invoke(self, *args, **kwargs):
        list_args = [self.bin_path, ] + self._prepare_args(*args, **kwargs)

        p = subprocess.Popen(list_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out, err, p.returncode

    def invoke_with_input(self, input, *args, **kwargs):
        list_args = [self.bin_path, ] + self._prepare_args(*args, **kwargs)
        print list_args
        p = subprocess.Popen(list_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(input=input)
        return out, err, p.returncode

@pytest.fixture(scope='function')
def runner(request):
    return Runner()
