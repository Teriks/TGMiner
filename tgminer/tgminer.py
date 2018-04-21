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
import json
import mimetypes
import os
import sys
import threading
import traceback
import uuid
from collections import OrderedDict

import fasteners
import pyrogram
import pyrogram.session
import whoosh.index
from pyrogram.api import functions as api_functions
from pyrogram.api import types as api_types
from pyrogram.client import message_parser
from slugify import slugify

import tgminer.config
import tgminer.fulltext
from tgminer import exits
from tgminer.cio import enc_print

# silence pyrogram message on start
pyrogram.session.Session.notice_displayed = True


class TGMinerClient:
    INDEX_DIR_NAME = 'indexdir'
    INTERPROCESS_MUTEX = 'tgminer_mutex'
    DIRECT_CHATS_SLUG = 'direct_chats'
    CHANNELS_DIR_NAME = 'channels'

    def __init__(self, config: tgminer.config.TGMinerConfig):

        session_path_dir = os.path.dirname(config.session_path)

        self._config = config

        if session_path_dir:
            os.makedirs(session_path_dir, exist_ok=True)

        pyrogram.Client.UPDATES_WORKERS = config.updates_workers
        pyrogram.Client.DOWNLOAD_WORKERS = config.download_workers

        self._client = pyrogram.Client(config.session_path,
                                       api_id=config.api_key.id,
                                       api_hash=config.api_key.hash)

        self._client.add_handler(pyrogram.RawUpdateHandler(self._update_handler))

        os.makedirs(config.data_dir, exist_ok=True)

        self._indexdir = os.path.join(config.data_dir, TGMinerClient.INDEX_DIR_NAME)

        # interprocess lock only
        self._index_lock_path = os.path.join(config.data_dir, TGMinerClient.INTERPROCESS_MUTEX)

        self._index_lock = threading.Lock()

        try:
            os.makedirs(self._indexdir)
            self._index = whoosh.index.create_in(self._indexdir, tgminer.fulltext.LogSchema)
        except OSError as e:
            if e.errno == errno.EEXIST:
                self._index = whoosh.index.open_dir(self._indexdir)

    @staticmethod
    def _get_media_ext(message: api_types.Message):
        if isinstance(message, api_types.Message):
            media = message.media
        else:
            media = message

        if isinstance(media, api_types.MessageMediaDocument):
            document = media.document

            if isinstance(document, api_types.Document):
                extension = ('.txt' if document.mime_type == 'text/plain' else
                             mimetypes.guess_extension(document.mime_type)
                             if document.mime_type else '.unknown')

                if extension is None:
                    # mimetypes.guess_extension does not figure out webp for some reason
                    return '.webp' if document.mime_type == 'image/webp' else '.none'
                return extension

        elif isinstance(media, (api_types.MessageMediaPhoto, api_types.Photo)):
            if isinstance(media, api_types.MessageMediaPhoto):
                photo = media.photo
            else:
                photo = media

            if isinstance(photo, api_types.Photo):
                return '.jpg'

        return '.none'

    @staticmethod
    def _get_user_alias(user: api_types.User):
        if user.first_name:
            return f'{user.first_name} {user.last_name}'.rstrip() if user.last_name else user.first_name
        return None

    @staticmethod
    def _get_log_username(user: api_types.User):

        user_id_part = f'[@{user.username}]' if user.username else ''

        if user.first_name:
            if user.last_name:
                return f'{user.first_name} {user.last_name} {user_id_part}'.rstrip()
            else:
                return f'{user.first_name} {user_id_part}'.rstrip()

        if user.last_name:
            return f'{user.last_name} {user_id_part}'.rstrip()

        if user.username:
            return user_id_part
        else:
            return 'None'

    def _index_log_message(self,
                           from_user: api_types.User,
                           to_user: api_types.User,
                           to_id: int,
                           media_info: str,
                           message_text: str,
                           chat_slug: str):

        # lock in process and multiprocess lock
        with self._index_lock, fasteners.InterProcessLock(self._index_lock_path):
            writer = self._index.writer()

            username = from_user.username

            alias = self._get_user_alias(from_user)

            if to_user:
                to_username = to_user.username
                to_alias = self._get_user_alias(to_user)
            else:
                to_username = None
                to_alias = None

            writer.add_document(username=username, alias=alias,
                                to_username=to_username, to_alias=to_alias,
                                media=media_info, message=message_text,
                                timestamp=datetime.datetime.now(),
                                chat=chat_slug, to_id=str(to_id))
            writer.commit()

    def _timestamp(self):
        return self._config.timestamp_format.format(datetime.datetime.now())

    def _filter_group_chat_check(self,
                                 title: str,
                                 chat_slug: str,
                                 chat_id: int,
                                 username: str,
                                 user_alias: str,
                                 user_id: int) -> bool:

        filter_title = self._config.group_filters.title
        filter_id = self._config.group_filters.id
        filter_title_slug = self._config.group_filters.title_slug

        filter_username = self._config.group_filters.username
        filter_user_alias = self._config.group_filters.user_alias
        filter_user_id = self._config.group_filters.user_id

        return not (filter_title.match(title) and
                    filter_id.match(str(chat_id)) and
                    filter_title_slug.match(chat_slug) and
                    filter_username.match(username) and
                    filter_user_alias.match(user_alias) and
                    filter_user_id.match(str(user_id)))

    def _filter_direct_chat_check(self,
                                  username: str,
                                  alias: str,
                                  from_id: int) -> bool:

        filter_username = self._config.direct_chat_filters.username
        filter_alias = self._config.direct_chat_filters.alias
        filter_id = self._config.direct_chat_filters.id

        return not (filter_username.match(username) and
                    filter_alias.match(alias) and
                    filter_id.match(str(from_id)))

    def _filter_users_check(self,
                            username: str,
                            alias: str,
                            from_id: int) -> bool:

        filter_username = self._config.user_filters.username
        filter_alias = self._config.user_filters.alias
        filter_id = self._config.user_filters.id

        return not (filter_username.match(username) and
                    filter_alias.match(alias) and
                    filter_id.match(str(from_id)))

    def _update_handler(self, client, update, users: dict, chats: dict):

        if not isinstance(update, (api_types.UpdateNewChannelMessage, api_types.UpdateNewMessage)):
            return

        update_message: api_types.Message = update.message

        if not isinstance(update_message, api_types.Message):
            return

        is_peer_user = isinstance(update_message.to_id, api_types.PeerUser)

        if is_peer_user and not self._config.log_direct_chats:
            return

        is_peer_channel = isinstance(update_message.to_id, api_types.PeerChannel)
        is_peer_chat = isinstance(update_message.to_id, api_types.PeerChat)

        if (is_peer_channel or is_peer_chat) and not self._config.log_group_chats:
            return

        user: api_types.User = users[update_message.from_id]

        user_name = user.username if user.username else ''

        user_alias = self._get_user_alias(user)
        log_user_name = self._get_log_username(user)

        chat_slug = TGMinerClient.DIRECT_CHATS_SLUG
        log_folder = os.path.join(self._config.data_dir, TGMinerClient.DIRECT_CHATS_SLUG)
        log_name = 'log.txt'

        to_user = None

        if is_peer_channel or is_peer_chat:
            channel = chats[update_message.to_id.channel_id] if is_peer_channel else chats[update_message.to_id.chat_id]
            to_id = channel.id

            chat_slug = slugify(channel.title)

            if self._filter_group_chat_check(title=channel.title,
                                             chat_slug=chat_slug,
                                             chat_id=channel.id,
                                             username=user_name,
                                             user_alias=user_alias,
                                             user_id=user.id):
                return

            log_folder = os.path.join(self._config.data_dir, TGMinerClient.CHANNELS_DIR_NAME,
                                      str(channel.id))
            log_name = chat_slug + '.log.txt'

        elif is_peer_user:

            to_user = users[update_message.to_id.user_id]
            to_id = to_user.id

            if self._filter_direct_chat_check(username=user_name,
                                              alias=user_alias,
                                              from_id=user.id):
                return
        else:
            return

        if self._filter_users_check(username=user_name,
                                    alias=user_alias,
                                    from_id=user.id):
            return

        if (self._config.download_photos or
                self._config.download_documents or
                self._config.write_raw_logs):
            os.makedirs(log_folder, exist_ok=True)

        indexed_media_info = None

        if isinstance(update_message.media, api_types.MessageMediaPhoto):

            parsed_message: pyrogram.Message = message_parser.parse_message(
                self._client,
                update.message,
                users,
                chats
            )

            indexed_media_info, indexed_message, short_log_entry = self._handle_photo_message(
                log_folder,
                log_user_name,
                update_message,
                parsed_message)

        elif isinstance(update_message.media, api_types.MessageMediaDocument):

            parsed_message: pyrogram.Message = message_parser.parse_message(
                self._client,
                update.message,
                users,
                chats
            )

            indexed_media_info, indexed_message, short_log_entry = self._handle_media_message(
                log_folder,
                log_user_name,
                update_message,
                parsed_message)

        else:
            indexed_message = update_message.message
            short_log_entry = f'{log_user_name}: {indexed_message}'

        self._index_log_message(from_user=user,
                                to_user=to_user,
                                to_id=to_id,
                                media_info=indexed_media_info,
                                message_text=indexed_message,
                                chat_slug=chat_slug)

        log_entry = '{} chat="{}" to_id="{}"{} | {}'.format(
            self._timestamp(), chat_slug, to_id,
            f' to {self._get_log_username(to_user)}' if to_user else '',
            short_log_entry)

        if self._config.chat_stdout:
            enc_print(log_entry)

        if self._config.write_raw_logs:
            with open(os.path.join(log_folder, log_name), 'a', encoding='utf-8') as file_handle:
                print(log_entry, file=file_handle)

    def _handle_media_message(self,
                              log_folder: str,
                              log_user_name: str,
                              update_message: api_types.Message,
                              parsed_message: pyrogram.Message):

        doc_file_path = os.path.abspath(
            os.path.join(log_folder, str(uuid.uuid4())) + self._get_media_ext(update_message))

        indexed_message: str = update_message.message

        filename_attr = next(
            (x for x in update_message.media.document.attributes
             if isinstance(x, api_types.DocumentAttributeFilename)), None)

        og_file_name = filename_attr.file_name if filename_attr else ''

        displayed_path = doc_file_path

        if self._config.download_documents and (not og_file_name or self._config.docname_filter.match(og_file_name)):
            self._client.download_media(parsed_message, file_name=doc_file_path, block=False)
        elif not self._config.download_documents:
            displayed_path = "DOCUMENT DOWNLOADS DISABLED"
        else:
            displayed_path = "DOCNAME_FILTER DISCARDED FILE"

        indexed_media_info = '(Document: "{}"{}: {})'.format(
            update_message.media.document.mime_type,
            f' - "{og_file_name}"',
            displayed_path)

        log_entry = (f'{log_user_name}: {indexed_media_info}' +
                     (f' Caption: {indexed_message}' if indexed_message else ''))

        return indexed_media_info, indexed_message, log_entry

    def get_chats_info(self) -> list:
        r = self._client.send(api_functions.messages.GetAllChats([]))

        data = []

        for i in r.chats:

            storage = os.path.abspath(os.path.join(self._config.data_dir, self.CHANNELS_DIR_NAME, str(i.id)))
            if not os.path.isdir(storage):
                storage = None

            data.append(OrderedDict([('type', type(i).__name__),
                                     ('id', i.id),
                                     ('title', i.title),
                                     ('slug', slugify(i.title)),
                                     ('storage', storage)]))

        return data

    def dump_chats_info(self, file):
        enc_print(json.dumps(self.get_chats_info(), indent=4, sort_keys=False), file=file)

    def get_peers_info(self) -> list:
        r = self._client.send(api_functions.users.GetUsers([*self._client.peers_by_id.values()]))

        data = []

        storage = os.path.abspath(os.path.join(self._config.data_dir, self.DIRECT_CHATS_SLUG))

        if not os.path.isdir(storage):
            storage = None

        for user in r:
            data.append(OrderedDict([('type', 'User'), ('id', user.id),
                                     ('alias', self._get_user_alias(user)),
                                     ('username', user.username),
                                     ('storage', storage)]))

        return data

    def dump_peers_info(self, file):
        enc_print(json.dumps(self.get_peers_info(), indent=4, sort_keys=False), file=file)

    def dump_chats_and_peers_info(self, file):
        enc_print(json.dumps(self.get_chats_info() + self.get_peers_info(), indent=4, sort_keys=False), file=file)

    def _handle_photo_message(self,
                              log_folder: str,
                              log_user_name: str,
                              update_message: api_types.Message,
                              parsed_message: pyrogram.Message):

        if self._config.download_photos:

            media_file_path = os.path.abspath(
                os.path.join(log_folder, str(uuid.uuid4())) + self._get_media_ext(update_message))

            self._client.download_media(parsed_message, file_name=media_file_path, block=False)

            indexed_media_info = f'(Photo: {media_file_path})'
        else:
            indexed_media_info = '(Photo: PHOTO DOWNLOADS DISABLED)'

        indexed_message = update_message.message

        log_entry = (f'{log_user_name}: {indexed_media_info}' +
                     (f' Caption: {update_message.message}' if update_message.message else ''))

        return indexed_media_info, indexed_message, log_entry

    def start(self):
        self._client.start()

    def stop(self):
        self._client.stop()

    def idle(self):
        self._client.idle()


def main():
    arg_parser = argparse.ArgumentParser(description='Passive telegram mining client.')

    arg_parser.add_argument('--config',
                            help='Path to TGMiner config file, defaults to "CWD/config.json". '
                                 'This will override the environmental variable TGMINER_CONFIG if it was defined.')

    arg_parser.add_argument('--show-chats',
                            help='Print information about the chats/channels you are in and exit. '
                                 'The information is printed as a JSON list containing objects.',
                            action='store_true')

    arg_parser.add_argument('--show-peers',
                            help='Print information about peer-users the client can see and exit. '
                                 'The information is printed as a JSON list containing objects. '
                                 'Using this with --show-chats combines the information from both options '
                                 'into one JSON list.',
                            action='store_true')

    args = arg_parser.parse_args()

    config_path = tgminer.config.get_config_path(args.config)

    if not os.path.isfile(config_path):
        enc_print(f'Config file "{config_path}" does not exist.', file=sys.stderr)
        exit(exits.EX_NOINPUT)

    try:
        # noinspection PyTypeChecker
        client = TGMinerClient(tgminer.config.TGMinerConfig(config_path))
    except tgminer.config.TGMinerConfigException as e:
        enc_print(str(e), file=sys.stderr)
        exit(exits.EX_CONFIG)
        return

    try:
        if args.show_chats or args.show_peers:
            try:
                client.start()
                if args.show_chats and args.show_peers:
                    client.dump_chats_and_peers_info(sys.stdout)
                elif args.show_chats:
                    client.dump_chats_info(sys.stdout)
                elif args.show_peers:
                    client.dump_peers_info(sys.stdout)
            finally:
                client.stop()
        else:
            client.start()
            client.idle()
    except Exception:
        enc_print('Client error:\n\n', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        exit(exits.EX_SOFTWARE)


if __name__ == '__main__':
    main()
