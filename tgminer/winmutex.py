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


import ctypes
import os.path
from ctypes import wintypes

_CreateMutex = ctypes.windll.kernel32.CreateMutexA
_CreateMutex.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCSTR]
_CreateMutex.restype = wintypes.HANDLE

_WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
_WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_WaitForSingleObject.restype = wintypes.DWORD

_ReleaseMutex = ctypes.windll.kernel32.ReleaseMutex
_ReleaseMutex.argtypes = [wintypes.HANDLE]
_ReleaseMutex.restype = wintypes.BOOL

_CloseHandle = ctypes.windll.kernel32.CloseHandle
_CloseHandle.argtypes = [wintypes.HANDLE]
_CloseHandle.restype = wintypes.BOOL


class NamedMutex:

    def __init__(self, name, acquired=False):
        if type(name) is str:
            self.name = ("Global\\" + os.path.basename(os.name)).encode()
        else:
            self.name = ("Global\\" + os.path.basename(os.name.decode())).encode()

        self._acquired = acquired
        ret = _CreateMutex(None, False, self.name)
        if not ret:
            raise ctypes.WinError()
        self._handle = ret

        if acquired:
            self.acquire()

    def acquire(self):
        ret = _WaitForSingleObject(self._handle, 0xFFFFFFFF)
        if ret in (0, 0x80):
            self._acquired = True
            return True
        elif ret == 0x102:
            self._acquired = False
            return False
        else:
            raise ctypes.WinError()

    def release(self):
        ret = _ReleaseMutex(self._handle)
        if not ret:
            raise ctypes.WinError()
        self._acquired = False

    def close(self):
        if self._handle is None:
            return
        ret = _CloseHandle(self._handle)
        if not ret:
            raise ctypes.WinError()
        self._handle = None

    __del__ = close

    def __repr__(self):
        return '{0}({1!r}, acquired={2})'.format(
            self.__class__.__name__, self.name, self._acquired)

    __str__ = __repr__

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
