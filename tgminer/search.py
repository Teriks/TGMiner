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
import kovit
import kovit.iters
import whoosh.index
from whoosh.qparser import QueryParser, sys

import tgminer.config
import tgminer.fulltext
from tgminer import exits
from tgminer.cio import enc_print


def query_limit(parser: argparse.ArgumentParser):
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


def markov_state_size(parser: argparse.ArgumentParser):
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
        description='Perform a full-text search over stored telegram messages.',
        prog='tgminer-search'
    )

    arg_parser.add_argument('--version', action='version', version='%(prog)s ' + tgminer.__version__)

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

    arg_parser.add_argument('--markov-optimize', default=None, choices=('accuracy', 'size'),
                            help='The default option "accuracy" produces a larger chain file where '
                                 'all trailing word/sequence probabilities are considered for every word in '
                                 'a message. This can result in a very large and slow to load chain if the '
                                 'state size is set to a high value. Setting this to "size" will cause '
                                 'trailing probabilities for the words inside the sequence that makes up a state '
                                 'to be discarded, except for the last word. This will make the chain smaller '
                                 'but results in more of an approximate model of the input messages.')

    args = arg_parser.parse_args()

    if args.markov_state_size is not None and args.markov is None:
        arg_parser.error('Must be using the --markov option to use --markov-state-size.')

    if args.markov_optimize is not None and args.markov is None:
        arg_parser.error('Must be using the --markov option to use --markov-optimize.')

    if args.markov_state_size is None:
        args.markov_state_size = 2

    if args.markov_optimize is None:
        args.markov_optimize = 'accuracy'

    config = None  # hush intellij highlighted undeclared variable use warning

    config_path = tgminer.config.get_config_path(args.config)

    if os.path.isfile(config_path):
        try:
            config = tgminer.config.TGMinerConfig(config_path)
        except tgminer.config.TGMinerConfigException as e:
            enc_print(str(e), file=sys.stderr)
            exit(exits.EX_CONFIG)
    else:
        enc_print(f'Cannot find tgminer config file: "{config_path}"')
        exit(exits.EX_NOINPUT)

    index = whoosh.index.open_dir(os.path.join(config.data_dir, 'indexdir'))

    index_lock_path = os.path.join(config.data_dir, 'tgminer_mutex')

    schema = tgminer.fulltext.LogSchema()

    query_parser = QueryParser('message', schema=schema)

    query = query_parser.parse(args.query)

    def result_iter():
        with fasteners.InterProcessLock(index_lock_path):
            with index.searcher() as searcher:
                yield from searcher.search(query,
                                           limit=None if args.limit < 1 else args.limit,
                                           sortedby='timestamp')

    if args.markov:
        split_by_spaces = re.compile('\s+')

        chain = kovit.Chain()

        if args.markov_optimize == 'accuracy':
            word_iter = kovit.iters.iter_window
        else:
            word_iter = kovit.iters.iter_runs

        anything = False
        for hit in result_iter():
            message = hit.get('message', None)
            if message:
                anything = True
                for start, next_items in word_iter(split_by_spaces.split(message), args.markov_state_size):
                    chain.add_to_bag(start, next_items)

        if not anything:
            enc_print('Query returned no messages!', file=sys.stderr)
            exit(exits.EX_SOFTWARE)

        try:
            with open(args.markov, 'w', encoding='utf-8') as m_out:
                chain.dump_json(m_out)
        except OSError as e:
            enc_print(f'Could not write markov chain to file "{args.markov}", error: {e}',
                      file=sys.stderr)
            exit(exits.EX_CANTCREAT)
    else:
        for hit in result_iter():

            message = hit.get('message', None)

            username = hit.get('username', None)
            alias = hit.get('alias', 'NO_ALIAS')

            to_username = hit.get('to_username', None)
            to_alias = hit.get('to_alias', None)
            to_id = hit.get('to_id')

            username_part = f' [@{username}]' if username else ''

            timestamp = config.timestamp_format.format(hit['timestamp'])

            chat_slug = hit['chat']

            media = hit.get('media', None)

            to_username_part = f' [@{to_username}]' if to_username else ''

            to_user_part = f' to {to_alias}{to_username_part}' if to_alias or to_username_part else ''

            if media:
                caption_part = f' Caption: {message}' if message else ''

                enc_print(
                    f'{timestamp} chat="{chat_slug}" to_id="{to_id}"{to_user_part} | {alias}{username_part}: {media}{caption_part}')
            else:
                enc_print(
                    f'{timestamp} chat="{chat_slug}" to_id="{to_id}"{to_user_part} | {alias}{username_part}: {hit["message"]}')


if __name__ == '__main__':
    main()
