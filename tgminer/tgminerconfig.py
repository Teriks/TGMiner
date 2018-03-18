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

import json

import jsoncomment


class TGMinerConfigException(Exception):
    def __init__(self, message):
        super().__init__(message)


class ApiKey:
    def __init__(self, id, hash):
        self.id = id
        self.hash = hash


class TGMinerConfig:
    def __init__(self, path):
        parser = jsoncomment.JsonComment(json)
        with open(path) as file:
            parsed_object = parser.load(file)

        if "api_key" not in parsed_object:
            raise TGMinerConfigException("api_key missing from TGMiner config.")

        if "id" not in parsed_object["api_key"]:
            raise TGMinerConfigException("id missing from api_key in TGMiner config.")

        if "hash" not in parsed_object["api_key"]:
            raise TGMinerConfigException("hash missing from api_key in TGMiner config.")

        self.api_key = ApiKey(parsed_object["api_key"]["id"], parsed_object["api_key"]["hash"])
        self.session_path = parsed_object.get("session_path", "tgminer")
        self.data_dir = parsed_object.get("data_dir", "data")
        self.chat_stdout = parsed_object.get("chat_stdout", False)
