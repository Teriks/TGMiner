TGMiner
=======

TGMiner is a telegram client bot for archiving and logging chat data from direct chats and group chats.

It makes all archived chat content searchable via full text indexing with the whoosh library for python.

TGMiner utilizes the **pyrogram** python telegram client library, and **whoosh** for full text search.

This project is experimental and probably barely usable or practical at the moment, currently in proof of concept mode.

Client
======

**tgminer** is the mining client and is packaged as a command named ``tgminer``,
see ``config.json.example`` for the config file example.  Also see ``tgminer --help``.

**tgminer** can be started with: ``tgminer --config path/config.json``.

The configuration file can also be specified with the environmental
variable ``TGMINER_CONFIG``. Defining the path with ``--config`` will
override the environmental variable.

If the session file mentioned in ``config.json`` is not created yet, you will be prompted
to log into telegram on the console, which will create the session file for your account.

After the session file is created you will not need to log into telegram again.

tgminer-search
==============

**tgminer-search** is the full text search tool for searching through the telegram logs.

**tgminer-search** needs to be pointed at your ``config.json`` file if it is not in the
current working directory, using ``tgminer-search --config path/config.json``.

You can also set the environmental variable ``TGMINER_CONFIG`` to the correct
file path and **tgminer-search** will use it unless ``--config`` is specified
explicitly.

Current searchable fields are:

* message (default search field, message text content) - Stemming Analysis matching
* alias (posting users alias) - Exact matches only
* username (posting users @username) - Exact matches only
* to_alias (receiving users alias) - Exact matches only
* to_username (receiving users @username) - Exact matches only
* to_id (Channel ID or User ID) - Exact matches only
* chat (slugified group chat name) - Exact matches only
* media (media field, see query examples..) - Stemming Analysis matching
* timestamp (chat log timestamp) - Exact matches and ranges


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

    # Try to generate a random message between X and Y characters long
    # These parameters are optional, but must always be specified together

    tgminer-markov chainfile.json --min-length 100 --max-length 500


    # Generate a chain with an alternate word state size

    tgminer-search "chat:my-funniest-chat *" --limit 0 --markov chainfile.json --markov-state-size 5


    # If your frequently getting an empty result, try bumping the number
    # of generation attempts up

    tgminer-markov chainfile.json --max-attempts 100


    # Try forever until something is generated at the risk of an
    # infinite loop, handle with a timeout by yourself or something

    tgminer-markov chainfile.json --max-attempts 0


Install
=======

Clone or download repository.

``sudo python setup.py install --upgrade``

Or:

``sudo pip install git+https://github.com/Teriks/TGMiner --upgrade``

Alternatively on Windows, run the command in an admin level command prompt without 'sudo'.