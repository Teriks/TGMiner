import argparse
import json

import markovify


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

        if value < 1:
            parser.error('Maximum attempts cannot be less than 1.')
        return value

    return test


def main():
    arg_parser = argparse.ArgumentParser(
        description='Read a markov chain file produced by tgminer-search --markov and generate random output.')

    arg_parser.add_argument('chain', help='JSON markov chain file, produced with: tgminer-search --markov.')

    arg_parser.add_argument('--max-attempts', default=10, type=max_attempts(arg_parser),
                            help='Maximum number of attempts to take at generating a message '
                                 'before returning an empty string. default is 10.')

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
        print('Error reading markov chain file "{}", message: {}'.format(args.chain, e))
        exit(1)
        return  # intellij wants this

    attempts = 0

    while True:
        if args.min_length is not None:
            message = m_text.make_short_sentence(args.max_length, args.min_length)
        else:
            message = m_text.make_sentence()

        if message:
            break

        attempts = attempts + 1

        if attempts == args.max_attempts:
            exit(2)

    print(message)


if __name__ == '__main__':
    main()
