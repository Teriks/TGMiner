import argparse
import random

import kovit

import tgminer
from tgminer import exits
from tgminer.cio import enc_print


def max_output_words(parser: argparse.ArgumentParser):
    def test(value):
        # noinspection PyBroadException
        try:
            value = int(value)
        except Exception:
            parser.error('Maximum output words must be an integer.')

        if value < 1:
            parser.error('Maximum output words cannot be less than 1.')
        return value

    return test


def max_attempts(parser: argparse.ArgumentParser):
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
                    'and generate a random message using the pre-processed chat data.',
        prog='tgminer-markov')

    arg_parser.add_argument('--version', action='version', version='%(prog)s ' + tgminer.__version__)

    arg_parser.add_argument('chain', help='JSON markov chain file, produced with: tgminer-search --markov.')

    arg_parser.add_argument('--max-attempts', default=10, type=max_attempts(arg_parser),
                            help='Maximum number of attempts to take at generating a message '
                                 'before returning an empty string. The default is 10, passing 0 '
                                 'means infinite but there is a chance of looping '
                                 'forever if you do that.')

    arg_parser.add_argument('--max-words', help='Max output length in words, default is 256.',
                            type=max_output_words(arg_parser), default=256)

    arg_parser.add_argument('--repeat', help='Keep generating words up until max word length.',
                            action='store_true', default=False)

    args = arg_parser.parse_args()

    m_chain = kovit.Chain()

    try:

        with open(args.chain, 'rb') as chain:
            m_chain.load_json(chain)
    except Exception as e:
        enc_print('Error reading markov chain file "{}", message: {}'.format(args.chain, e))
        exit(exits.EX_NOINPUT)
        return  # intellij wants this

    attempts = 0

    while True:

        message = ' '.join(m_chain.walk(args.max_words, repeat=args.repeat,
                                        start_chooser=lambda: m_chain.random_start(dead_end_ok=False)))

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
