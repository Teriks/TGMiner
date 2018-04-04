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

import argparse
import os.path
import re

import fasteners

import markovify

import whoosh.index
from whoosh.qparser import QueryParser, sys

import tgminer.fulltext
import tgminer.config

from tgminer import exits


def query_limit(parser):
    def test(value):
        # noinspection PyBroadException
        try:
            value = int(value)
        except Exception:
            parser.error('Query results limit must be an integer.')

        if value < 0:
            parser.error('Query results limit cannot be less than 0.')
        return value

    return test


def markov_state_size(parser):
    def test(value):
        # noinspection PyBroadException
        try:
            value = int(value)
        except Exception:
            parser.error('Markov state size must be an integer.')

        if value < 1:
            parser.error('Markov state size cannot be less than 1.')
        return value

    return test


def main():
    arg_parser = argparse.ArgumentParser(
        description='Perform a full-text search over stored telegram messages.'
    )

    arg_parser.add_argument('query', help='Query text.')

    arg_parser.add_argument('--config',
                            help='Path to TGMiner config file, defaults to "CWD/config.json". '
                                 'This will override the environmental variable '
                                 'TGMINER_CONFIG if it was defined.')

    arg_parser.add_argument('--limit', help='Results limit, 0 for infinite. Default is 10.',
                            type=query_limit(arg_parser),
                            default=10)

    arg_parser.add_argument('--markov',
                            help='Generate a markov chain file from the messages in your query results.',
                            metavar='OUT_FILE')

    arg_parser.add_argument('--markov-state-size', default=None,
                            help='The number of words to use in the markov model\'s state, default is 2. '
                                 'Must be used in conjunction with --markov.',
                            type=markov_state_size(arg_parser))

    args = arg_parser.parse_args()

    if args.markov_state_size is not None and args.markov is None:
        arg_parser.error('Must be using the --markov option to use --markov-state-size.')

    if args.markov_state_size is None:
        args.markov_state_size = 2

    config = None  # hush intellij highlighted undeclared variable use warning

    config_path = tgminer.config.get_config_path(args.config)

    if os.path.isfile(config_path):
        try:
            config = tgminer.config.TGMinerConfig(config_path)
        except tgminer.config.TGMinerConfigException as e:
            print(str(e), file=sys.stderr)
            exit(exits.EX_CONFIG)
    else:
        print('Cannot find tgminer config file: "{}"'.format(config_path))
        exit(exits.EX_NOINPUT)

    index = whoosh.index.open_dir(os.path.join(config.data_dir, 'indexdir'))

    index_lock_path = os.path.join(config.data_dir, 'tgminer_mutex')

    schema = tgminer.fulltext.LogSchema()

    query_parser = QueryParser('message', schema=schema)

    query = query_parser.parse(args.query)

    markov_input = []

    with fasteners.InterProcessLock(index_lock_path):
        with index.searcher() as searcher:

            search = searcher.search(query,
                                     limit=None if args.limit < 1 else args.limit,
                                     sortedby='timestamp')
            for hit in search:

                message = hit.get('message', None)
                if args.markov:
                    if message:
                        markov_input = markov_input + markovify.split_into_sentences(message)
                    continue

                username = hit.get('username', None)
                alias = hit.get('alias', 'NO_ALIAS')

                to_username = hit.get('to_username', None)
                to_alias = hit.get('to_alias', None)
                to_id = hit.get('to_id')

                username_part = ' [@{}]'.format(username) if username else ''

                timestamp = config.timestamp_format.format(hit['timestamp'])

                chat_slug = hit['chat']

                media = hit.get('media', None)

                to_username_part = ' [@{}]'.format(to_username) if to_username else ''

                if to_alias or to_username_part:
                    to_user_part = ' to {}{}'.format(to_alias, to_username_part)
                else:
                    to_user_part = ''

                if media:
                    caption_part = ' Caption: {}'.format(message) if message else ''

                    print('{} chat="{}" to_id="{}"{} | {}{}: {}{}'
                          .format(timestamp, chat_slug, to_id, to_user_part,
                                  alias,
                                  username_part, media,
                                  caption_part))
                else:
                    print('{} chat="{}" to_id="{}"{} | {}{}: {}'
                          .format(timestamp, chat_slug, to_id, to_user_part,
                                  alias,
                                  username_part,
                                  hit['message']))

    if args.markov:
        split_by_spaces = re.compile('\s')

        if len(markov_input) == 0:
            print('Query returned no messages!', file=sys.stderr)
            exit(exits.EX_SOFTWARE)

        for idx, v in enumerate(markov_input):
            markov_input[idx] = split_by_spaces.split(v)

        text = markovify.Text(input_text=None,
                              parsed_sentences=markov_input,
                              state_size=args.markov_state_size)

        try:
            with open(args.markov, 'w', encoding='utf-8') as m_out:
                m_out.write(text.to_json())
        except OSError as e:
            print('Could not write markov chain to file "{}", error: {}'
                  .format(args.markov, e), file=sys.stderr)
            exit(exits.EX_CANTCREAT)


if __name__ == '__main__':
    main()
