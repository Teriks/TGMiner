# Copyright (c) 2018, Teriks
# All rights reserved.
#
# TGMiner is distributed under the following BSD 3-Clause License
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import errno
import os

import fcntl


class NamedMutex:
    def __init__(self, path, acquired=False):
        self._path = path
        self._fd = None
        if acquired:
            self.acquire()

    def acquire(self):
        while self._fd is None:
            fd = os.open(self._path, os.O_CREAT | os.O_WRONLY, 0o666)
            try:
                fcntl.lockf(fd, fcntl.LOCK_EX)

                try:
                    stat1 = os.stat(self._path)
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise
                else:
                    stat2 = os.fstat(fd)
                    if stat1.st_dev == stat2.st_dev \
                            and stat1.st_ino == stat2.st_ino:
                        self._fd = fd

            finally:
                if self._fd is None:
                    os.close(fd)

    def __enter__(self):
        if self._fd is None:
            raise ValueError('This lock is released')

        return self

    def __repr__(self):
        repr_str = '<'
        if self._fd is None:
            repr_str += 'released'
        else:
            repr_str += 'acquired'

        repr_str += ' lock file ' + repr(self._path) + '>'
        return repr_str

    __str__ = __repr__

    def release(self):
        if self._fd is None:
            raise ValueError('This lock file is already released')

        try:
            os.remove(self._path)
        finally:
            try:
                os.close(self._fd)
            finally:
                self._fd = None

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
