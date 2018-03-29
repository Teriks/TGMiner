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
import re

import dschema
import jsoncomment


class TGMinerConfigException(Exception):
    def __init__(self, message):
        super().__init__(message)


class TGMinerConfig:
    def __init__(self, path):
        self.config_path = path

        self._validator = dschema.Validator({
            'api_key': {
                'id': dschema.prop(required=True, type=int),
                'hash': dschema.prop(required=True),
                dschema.Required: True
            },
            'session_path': dschema.prop(default='tgminer'),
            'data_dir': dschema.prop(default='data'),
            'chat_stdout': dschema.prop(default=False, type=bool),
            'timestamp_format': dschema.prop(default='({:%Y/%m/%d - %I:%M:%S %p})'),

            'group_filters': {
                'title': dschema.prop(default='.*', type='regex'),
                'title_slug': dschema.prop(default='.*', type='regex'),
                'id': dschema.prop(default='.*', type='regex'),

                'username': dschema.prop(default='.*', type='regex'),
                'user_alias': dschema.prop(default='.*', type='regex'),
                'user_id': dschema.prop(default='.*', type='regex')
            },

            'direct_chat_filters': {
                'username': dschema.prop(default='.*', type='regex'),
                'alias': dschema.prop(default='.*', type='regex'),
                'id': dschema.prop(defaults='.*', type='regex')
            },

            'user_filters': {
                'username': dschema.prop(default='.*', type='regex'),
                'alias': dschema.prop(default='.*', type='regex'),
                'id': dschema.prop(defaults='.*', type='regex')
            },

            'log_direct_chats': dschema.prop(default=True, type=bool)
        })

        def regex_type(value):
            return re.compile(value)

        self._validator.add_type('regex', regex_type)

        self._config = None

        self.load()

    def load(self):
        parser = jsoncomment.JsonComment(json)
        with open(self.config_path) as file:
            parsed_object = parser.load(file)

        try:
            self._config = self._validator.validate(parsed_object, namespace=True, copy=False)
        except dschema.ValidationError as e:
            raise TGMinerConfigException("Config Error: " + str(e))

        self.__dict__.update(self._config.__dict__)

    def __repr__(self):
        return str(self._config)

    def __str__(self):
        return self.__repr__()
