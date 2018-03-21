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
import datetime
import errno
import mimetypes
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import fasteners
import pyrogram
import pyrogram.api
import pyrogram.api.types
import pyrogram.session
import sys
import whoosh.index
from slugify import slugify
from pyrogram.crypto import AES
import pyrogram.api.functions
import pyrogram.api.errors
from hashlib import sha256

import tgminer.fulltext
from tgminer.tgminerconfig import TGMinerConfig, TGMinerConfigException

# silence pyrogram message on start
pyrogram.session.Session.notice_displayed = True


class TGMinerClient:
    INDEX_DIR_NAME = "indexdir"
    INTERPROCESS_MUTEX = "tgminer_mutex"
    DIRECT_CHATS_SLUG = "direct_chats"
    CHANNELS_DIR_NAME = "channels"

    def __init__(self, config):

        session_path_dir = os.path.dirname(config.session_path)

        self._config = config

        if session_path_dir != "":
            try:
                os.makedirs(session_path_dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        pyrogram.Client.DOWNLOAD_WORKERS = 4
        self._client = pyrogram.Client(config.session_path, api_key=(config.api_key.id, config.api_key.hash))

        self._client.set_update_handler(self._update_handler)

        try:
            os.makedirs(config.data_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        self._indexdir = os.path.join(config.data_dir, TGMinerClient.INDEX_DIR_NAME)

        # interprocess lock only
        self._index_lock_path = os.path.join(config.data_dir, TGMinerClient.INTERPROCESS_MUTEX)

        self._index_lock = threading.Lock()

        if not os.path.exists(self._indexdir):
            os.makedirs(self._indexdir)
            self._index = whoosh.index.create_in(self._indexdir, tgminer.fulltext.LogSchema)
        else:
            self._index = whoosh.index.open_dir(self._indexdir)

    @staticmethod
    def get_media_ext(message):
        """
        :type message: pyrogram.api.types.Message
        :return: str file extension
        """
        if isinstance(message, pyrogram.api.types.Message):
            media = message.media
        else:
            media = message

        if isinstance(media, pyrogram.api.types.MessageMediaDocument):
            document = media.document

            if isinstance(document, pyrogram.api.types.Document):
                extension = ".txt" if document.mime_type == "text/plain" else \
                    mimetypes.guess_extension(document.mime_type) if document.mime_type else ".unknown"

                if extension is None:
                    if document.mime_type == "image/webp":
                        # mimetypes.guess_extension does not figure out webp for some reason
                        return ".webp"
                    else:
                        return ".none"
                return extension

        elif isinstance(media, (pyrogram.api.types.MessageMediaPhoto, pyrogram.api.types.Photo)):
            if isinstance(media, pyrogram.api.types.MessageMediaPhoto):
                photo = media.photo
            else:
                photo = media

            if isinstance(photo, pyrogram.api.types.Photo):
                return ".jpg"

        return ".none"

    @staticmethod
    def _get_user_alias(user):
        """
       :type user: pyrogram.api.types.User
       """
        if user.first_name is not None:
            if user.last_name is not None:
                return "{} {}".format(
                    user.first_name, user.last_name)
            else:
                return user.first_name
        return None

    @staticmethod
    def _get_log_username(user):
        """
        :type user: pyrogram.api.types.User
        """
        user_id_part = "[@{}]".format(user.username) if user.username else ""

        if user.first_name is not None:
            if user.last_name is not None:
                return "{} {} {}".format(
                    user.first_name, user.last_name, user_id_part).rstrip()
            else:
                return "{} {}".format(user.first_name, user_id_part).rstrip()

        if user.last_name is not None:
            return "{} {}".format(user.last_name, user_id_part).rstrip()

        if user.username is not None:
            return user_id_part
        else:
            return "None"

    def _write_index_msg(self, user, to_user, media, message, chat_slug, to_id):
        """
        :type chat_slug: str
        :type message: str
        :type media: str
        :type to_user: pyrogram.api.types.User
        :type user: pyrogram.api.types.User
        """

        # lock in process and multiprocess lock
        with self._index_lock, fasteners.InterProcessLock(self._index_lock_path):
            writer = self._index.writer()

            username = user.username

            alias = self._get_user_alias(user)

            if to_user:
                to_username = to_user.username

                to_alias = self._get_user_alias(to_user)
            else:
                to_username = None
                to_alias = None

            writer.add_document(username=username, alias=alias,
                                to_username=to_username, to_alias=to_alias,
                                media=media, message=message,
                                timestamp=datetime.datetime.now(),
                                chat=chat_slug, to_id=to_id)
            writer.commit()

    def _timestamp(self):
        return self._config.timestamp_format.format(datetime.datetime.now())

    def _update_handler(self, client, update, users, chats):

        if not isinstance(update, (pyrogram.api.types.UpdateNewChannelMessage, pyrogram.api.types.UpdateNewMessage)):
            return

        message = update.message

        if not isinstance(message, pyrogram.api.types.Message):
            return

        is_peer_channel = isinstance(message.to_id, pyrogram.api.types.PeerChannel)
        is_peer_chat = isinstance(message.to_id, pyrogram.api.types.PeerChat)
        is_peer_user = isinstance(message.to_id, pyrogram.api.types.PeerUser)

        user = users[message.from_id]

        user_name = self._get_log_username(user)

        chat_slug = TGMinerClient.DIRECT_CHATS_SLUG
        log_folder = os.path.join(self._config.data_dir, TGMinerClient.DIRECT_CHATS_SLUG)
        log_name = "log.txt"
        channel = None

        if is_peer_channel or is_peer_chat:
            channel = chats[message.to_id.channel_id] if is_peer_channel else chats[message.to_id.chat_id]
            chat_slug = slugify(channel.title)
            log_folder = os.path.join(self._config.data_dir, TGMinerClient.CHANNELS_DIR_NAME,
                                      str(channel.id))
            log_name = chat_slug + ".log.txt"

        try:
            os.makedirs(log_folder)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        log_file = os.path.join(log_folder, log_name)

        indexed_media_info = None

        if isinstance(message.media, pyrogram.api.types.MessageMediaPhoto):
            name = str(uuid.uuid4())

            media_file_path = os.path.abspath(os.path.join(log_folder, name) + self.get_media_ext(message))

            indexed_media_info = "(Photo: {})".format(media_file_path)

            indexed_message = message.message

            log_entry = "{}: {}{}".format(user_name, indexed_media_info, " Caption: {}"
                                          .format(message.message) if message.message else "")

            self._client.download_media(message, file_name=media_file_path)

        elif isinstance(message.media, pyrogram.api.types.MessageMediaDocument):
            name = str(uuid.uuid4())

            media_file_path = os.path.abspath(os.path.join(log_folder, name) + self.get_media_ext(message))

            indexed_media_info = "(Document: \"{}\": {})".format(message.media.document.mime_type, media_file_path)

            indexed_message = message.message

            log_entry = "{}: {}{}".format(user_name, indexed_media_info, " Caption: {}"
                                          .format(message.message) if message.message else "")

            self._client.download_media(message, file_name=media_file_path)

        else:
            indexed_message = message.message
            log_entry = "{}: {}".format(user_name, message.message)

        if is_peer_user:
            to_user = users[message.to_id.user_id]
        else:
            to_user = None

        to_id = str(channel.id if channel else message.to_id.user_id)

        self._write_index_msg(user, to_user, indexed_media_info, indexed_message, chat_slug, to_id)

        log_entry = "{} chat=\"{}\" to_id=\"{}\"{} | {}".format(self._timestamp(), chat_slug, to_id,
                                                                " to {}".format(
                                                                    self._get_log_username(to_user)) if to_user else "",
                                                                log_entry)

        if self._config.chat_stdout:
            print(log_entry)

        with open(log_file, "a", encoding='utf-8') as fhandle:
            print(log_entry, file=fhandle)

    def start(self):
        self._client.start()
        self._client.idle()


def main():
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument("--config", help="Path to TGMiner config file, defaults to \"CWD/config.json\".",
                            default=os.path.join(os.getcwd(), "config.json"))

    args = arg_parser.parse_args()

    if os.path.isfile(args.config):
        try:
            TGMinerClient(TGMinerConfig(args.config)).start()
        except TGMinerConfigException as e:
            print(str(e), file=sys.stderr)
            exit(3)
    else:
        print("Config file \"{}\" does not exist.".format(os.path.abspath(args.config)), file=sys.stderr)
        exit(2)


if __name__ == "__main__":
    main()
