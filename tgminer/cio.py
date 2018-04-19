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

import sys
import os


def enc_print(*args, sep: str = ' ', end: str = '\n', file=None, flush=False, encoding: str = 'utf-8'):
    """Prints with default encoding to terminals, prints with a specific encoding to everything else.

    :param args: Arguments to print
    :param sep: Separator
    :param end: Terminator
    :param file: Print to file object
    :param flush: Flush after write? flush is always called on ttys.
    :param encoding: Write with encoding, apply to anything that is not a tty.
    :return:
    """

    if not file:
        file = sys.stdout
        raw_file = file.buffer
    else:
        raw_file = file

        if hasattr(raw_file, 'buffer'):
            raw_file = raw_file.buffer

    atty = hasattr(file, 'fileno') and os.isatty(file.fileno())

    if sep is None:
        sep = ''

    if end is None:
        end = ''

    if not atty:
        raw_file.write((sep.join(args) + end).encode(encoding))
    else:
        flush = True
        if hasattr(file, 'encoding'):
            encoding = file.encoding
        else:
            encoding = sys.getdefaultencoding()

        raw_file.write((sep.join(args) + end).encode(encoding))

    if hasattr(file, 'flush') and flush:
        file.flush()
