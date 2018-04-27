About TGMiner
=============

TGMiner is a telegram client bot for archiving and logging chat data from direct chats and group chats.

It makes all archived chat content searchable via full text indexing with the whoosh library for python.

TGMiner utilizes the **pyrogram** python telegram client library, and **whoosh** for full text search.

The client (tgminer)
====================

**tgminer** is the mining client and is packaged as a command named ``tgminer``,
see ``config.json.example`` for the config file example.  Also see ``tgminer --help``.


Configuring and Running
-----------------------

**tgminer** can be started with: ``tgminer --config path/config.json``.

The configuration file can also be specified with the environmental
variable ``TGMINER_CONFIG``. Defining the path with ``--config`` will
override the environmental variable.

If neither ``TGMINER_CONFIG`` or ``--config`` is used, **tgminer** will look
in the current working directory for a file named ``config.json``.

If the session file mentioned in ``config.json`` is not created yet, you will be prompted
to log into telegram on the console, which will create the session file for your account.

After the session file is created you will not need to log into telegram again.


Listing Chats and Peers
-----------------------

The client can print information about the chats you are in and then
exit with the use of ``--show-chats``.


``--show-chats`` will print the information as a JSON list like this one:


The **storage** field indicates where TGMiner is storing plain text logs and
media downloads for the chat/channel.

If **storage** does not exist (IE. is **null**) that means that TGMiner has not stored any
plain text logs or media for the chat, either because of how you configured TGMiner
or because there has been no activity in that chat since TGMiner was first started.


.. code-block:: json

    [
        {
            "type": "Chat",
            "id": 123456789,
            "title": "Chat Title (And maybe funny special characters)",
            "slug": "chat-title",
            "storage": "data_dir/channels/123456789"
        },
        {
            "type": "Channel",
            "id": 987654321,
            "title": "Channel Title (And maybe funny special characters)",
            "slug": "channel-title",
            "storage": "data_dir/channels/987654321"
        }
    ]

It can also print information about the peer-users the client can see, IE.
People you have opened direct chats with.  Using ``--show-peers``.

``--show-peers`` will also print a JSON list.


.. code-block:: json

    [
        {
            "type": "User",
            "id": 123456789,
            "alias": "Firstname Lastname",
            "username": "raw_username",
            "storage": "data_dir/direct_chats"
        },
        {
            "type": "User",
            "id": 987654321,
            "title": "Firstname Lastname2",
            "slug": "raw_username2",
            "storage": "data_dir/direct_chats"
        }
    ]


If you use ``--show-chats`` and ``--show-peers`` at the same time, the two
JSON lists will be merged with chats/channels always appearing first regardless
of argument order.

Example:

.. code-block:: json

    [
        {
            "type": "Chat",
            "id": 123456789,
            "title": "Chat Title (And maybe funny special characters)",
            "slug": "chat-title",
            "storage": "data_dir/channels/123456789"
        },
        {
            "type": "Channel",
            "id": 987654321,
            "title": "Channel Title (And maybe funny special characters)",
            "slug": "channel-title",
            "storage": "data_dir/channels/987654321"
        },
        {
            "type": "User",
            "id": 123456789,
            "alias": "Firstname Lastname",
            "username": "raw_username",
            "storage": "data_dir/direct_chats"
        },
        {
            "type": "User",
            "id": 987654321,
            "title": "Firstname Lastname2",
            "slug": "raw_username2",
            "storage": "data_dir/direct_chats"
        }
    ]


Current Help Output
-------------------

.. code-block::

    usage: tgminer [-h] [--version] [--config CONFIG] [--show-chats]
                   [--show-peers]

    Passive telegram mining client.

    optional arguments:
      -h, --help       show this help message and exit
      --version        show program's version number and exit
      --config CONFIG  Path to TGMiner config file, defaults to "CWD/config.json".
                       This will override the environmental variable
                       TGMINER_CONFIG if it was defined.
      --show-chats     Print information about the chats/channels you are in and
                       exit. The information is printed as a JSON list containing
                       objects.
      --show-peers     Print information about peer-users the client can see and
                       exit. The information is printed as a JSON list containing
                       objects. Using this with --show-chats combines the
                       information from both options into one JSON list.


tgminer-search
==============

**tgminer-search** is the full text search tool for searching through the telegram logs.

**tgminer-search** needs to be pointed at your ``config.json`` file if it is not in the
current working directory, using ``tgminer-search --config path/config.json``.

You can also set the environmental variable ``TGMINER_CONFIG`` to the correct
file path and **tgminer-search** will use it unless ``--config`` is specified
explicitly.

Current searchable fields are:

* **message** (default search field, message text content) - Stemming Analysis matching
* **alias** (posting users alias) - Exact matches only
* **username** (posting users @username) - Exact matches only
* **to_alias** (receiving users alias) - Exact matches only
* **to_username** (receiving users @username) - Exact matches only
* **to_id** (Channel ID or User ID) - Exact matches only
* **chat** (slugified group chat name) - Exact matches only
* **media** (media field, see query examples..) - Stemming Analysis matching
* **timestamp** (chat log timestamp) - Exact matches and ranges


**whoosh** is used to provide full text search

Query Syntax: http://whoosh.readthedocs.io/en/latest/querylang.html

Query Examples:

.. code-block:: bash

    # the --limit argument of tgminer-search can be set to 0, which
    # will cause your queries to return an infinite amount of results.
    # the default --limit value is 10

    # search every logged message by content

    tgminer-search "content to search for"

    # search message content of post by @someones_username or alias

    tgminer-search "username:someones_username message content"

    tgminer-search "alias:'Firstname Lastname' message content"

    tgminer-search "alias:FirstnameNoLastname message content"

    # search photos from @someones_username or alias

    tgminer-search "media:Photo username:someones_username"

    tgminer-search "media:Photo alias:'Firstname Lastname'"

    tgminer-search "media:Photo alias:FirstnameNoLastname"

    # search documents from @someones_username or alias

    tgminer-search "media:Document username:someones_username"

    tgminer-search "media:Document alias:'Firstname Lastname'"

    tgminer-search "media:Document alias:FirstnameNoLastname"

    # search every document or photo from every chat

    tgminer-search "media:Document caption content"

    tgminer-search "media:Photo caption content"

    # search specific chats

    tgminer-search "to_alias:'Firstname Lastname' message content"

    tgminer-search "to_alias:FirstnameNoLastname message content"

    tgminer-search "to_username:someones_username message content"

    tgminer-search "chat:slugified-chat-name message content"

    # search all direct to contact chats only

    tgminer-search "chat:direct-chats message content"

    # search for all documents and photos from a user across all chats

    tgminer-search "media:Document OR media:Photo AND username:some_username"


Current Help Output
-------------------

.. code-block::

    usage: tgminer-search [-h] [--version] [--config CONFIG] [--limit LIMIT]
                          [--markov OUT_FILE]
                          [--markov-state-size MARKOV_STATE_SIZE]
                          [--markov-optimize {accuracy,size}]
                          query

    Perform a full-text search over stored telegram messages.

    positional arguments:
      query                 Query text.

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --config CONFIG       Path to TGMiner config file, defaults to
                            "CWD/config.json". This will override the
                            environmental variable TGMINER_CONFIG if it was
                            defined.
      --limit LIMIT         Results limit, 0 for infinite. Default is 10.
      --markov OUT_FILE     Generate a markov chain file from the messages in your
                            query results.
      --markov-state-size MARKOV_STATE_SIZE
                            The number of words to use in the markov model's
                            state, default is 2. Must be used in conjunction with
                            --markov.
      --markov-optimize {accuracy,size}
                            The default option "accuracy" produces a larger chain
                            file where all trailing word/sequence probabilities
                            are considered for every word in a message. This can
                            result in a very large and slow to load chain if the
                            state size is set to a high value. Setting this to
                            "size" will cause trailing probabilities for the words
                            inside the sequence that makes up a state to be
                            discarded, except for the last word. This will make
                            the chain smaller but results in more of an
                            approximate model of the input messages.

tgminer-markov
==============

You can produce humorous random chat messages based off your telegram chat logs
using a combination of the packaged ``tgminer-search`` and ``tgminer-markov`` commands.


.. code-block:: bash

    # Dump a whole chat by its slugified name into a markov chain
    # using the "*" query operator.

    # Setting --limit to 0 causes all saved messages to be dumped.

    tgminer-search "chat:my-funniest-chat *" --limit 0 --markov chainfile.json

    # Generate a random message from the markov chain

    tgminer-markov chainfile.json

    # Try to generate a random message with a max length of 500 words

    tgminer-markov chainfile.json --max-words 500

    # Keep generating text until 500 words have been generated

    tgminer-markov chainfile.json --max-words 500 --repeat

    # Generate a chain with an alternate word state size

    tgminer-search "chat:my-funniest-chat *" --limit 0 --markov chainfile.json --markov-state-size 5


    # If your frequently getting an empty result, try bumping the number
    # of generation attempts up

    tgminer-markov chainfile.json --max-attempts 100


    # Try forever until something is generated at the risk of an
    # infinite loop, handle with a timeout by yourself or something

    tgminer-markov chainfile.json --max-attempts 0


Current Help Output
-------------------

.. code-block::

    usage: tgminer-markov [-h] [--version] [--max-attempts MAX_ATTEMPTS]
                          [--max-words MAX_WORDS] [--repeat]
                          chain

    Read a markov chain file produced by tgminer-search --markov and generate a
    random message using the pre-processed chat data.

    positional arguments:
      chain                 JSON markov chain file, produced with: tgminer-search
                            --markov.

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --max-attempts MAX_ATTEMPTS
                            Maximum number of attempts to take at generating a
                            message before returning an empty string. The default
                            is 10, passing 0 means infinite but there is a chance
                            of looping forever if you do that.
      --max-words MAX_WORDS
                            Max output length in words, default is 256.
      --repeat              Keep generating words up until max word length.


Install
=======

Clone or download repository.

``sudo python setup.py install``

Or:

``sudo pip install https://github.com/Teriks/TGMiner/archive/master.zip --upgrade``

Alternatively on Windows, run the command in an admin level command prompt without 'sudo'.