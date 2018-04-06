import argparse
import json

import markovify

from tgminer import exits
from tgminer.cio import enc_print


def min_output_length(parser):
    def test(value):
        # noinspection PyBroadException
        try:
            value = int(value)
        except Exception:
            parser.error('Minimum output length must be an integer.')

        if value < 1:
            parser.error('Minimum output length cannot be less than 1.')
        return value

    return test


def max_output_length(parser):
    def test(value):
        # noinspection PyBroadException
        try:
            value = int(value)
        except Exception:
            parser.error('Maximum output length must be an integer.')

        if value < 1:
            parser.error('Maximum output length cannot be less than 1.')
        return value

    return test


def max_attempts(parser):
    def test(value):
        # noinspection PyBroadException
        try:
            value = int(value)
        except Exception:
            parser.error('Maximum attempts must be an integer.')

        if value < 0:
            parser.error('Maximum attempts cannot be less than 0.')
        return value

    return test


def main():
    arg_parser = argparse.ArgumentParser(
        description='Read a markov chain file produced by tgminer-search --markov '
                    'and generate a random message using the pre-processed chat data.')

    arg_parser.add_argument('chain', help='JSON markov chain file, produced with: tgminer-search --markov.')

    arg_parser.add_argument('--max-attempts', default=10, type=max_attempts(arg_parser),
                            help='Maximum number of attempts to take at generating a message '
                                 'before returning an empty string. The default is 10, passing 0 '
                                 'means infinite but there is a chance of looping '
                                 'forever if you do that.')

    min_max_group = arg_parser.add_argument_group(
        description='The following are optional, but must be specified together.')

    min_max_group.add_argument('--min-length', help='Min output length in characters.',
                               type=min_output_length(arg_parser))
    min_max_group.add_argument('--max-length', help='Max output length in characters.',
                               type=max_output_length(arg_parser))

    args = arg_parser.parse_args()

    if len([x for x in (args.min_length, args.max_length) if x is not None]) == 1:
        arg_parser.error('--min-length and --max-length must be given together')

    try:
        with open(args.chain, 'r', encoding='utf-8') as chain:
            m_text = markovify.Text.from_dict(json.load(chain))
    except Exception as e:
        enc_print('Error reading markov chain file "{}", message: {}'.format(args.chain, e))
        exit(exits.EX_NOINPUT)
        return  # intellij wants this

    attempts = 0

    while True:
        if args.min_length is not None:
            message = m_text.make_short_sentence(args.max_length, args.min_length, tries=1)
        else:
            message = m_text.make_sentence(tries=1)

        if message:
            break

        if args.max_attempts == 0:
            continue

        attempts = attempts + 1

        if attempts == args.max_attempts:
            exit(exits.EX_SOFTWARE)

    enc_print(message)


if __name__ == '__main__':
    main()
