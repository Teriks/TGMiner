TGMiner
=======

TGMiner is a telegram client bot for archiving and logging chat data from direct chats and group chats.

It makes all archived chat content searchable via full text indexing with the whoosh library for python.

This project is experimental and probably barely usable or practical at the moment, currently in proof of concept mode.

Client
======

tgminer is the mining client and is packaged as an installed command named ``tgminer``,
see ``config.json.example`` for the config file example.  Also see ``tgminer --help``

If the session file mentioned in ``config.json`` is not created yet, you will be prompted
to log into telegram on the console, which will create the session file for your account.

After the session file is created you will not need to log into telegram again.

tgminer-search
==============

tgminer-search is the full text search tool for searching through the telegram logs.

tgminer-search needs to be pointed at your ``config.json`` file if it is not in the current working directory, using ``tgminer-search --config path/config.json``.

Current searchable fields are:

* message (default search field, message text content) - Stemming Analysis matching
* alias (posting users alias) - Exact matches only
* username (posting users @username) - Exact matches only
* to_alias (receiving users alias) - Exact matches only
* to_username (receiving users @username) - Exact matches only
* chat (slugified group chat name) - Exact matches only
* media (media field, see query examples..) - Stemming Analysis matching
* timestamp (chat log timestamp) - Exact matches and ranges


whoosh is used to provide full text search

.. _Whoosh Query Syntax: http://whoosh.readthedocs.io/en/latest/querylang.html

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


Install
=======

Clone or download repository.

``sudo python setup.py install``

Alternatively on Windows, run the command in an admin level command prompt without 'sudo'.