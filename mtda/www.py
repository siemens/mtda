# ---------------------------------------------------------------------------
# Web service for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2025 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import asyncio
import json
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.escape
import os
import threading
import uuid
import secrets
from urllib.parse import urlparse

import mtda.constants as CONSTS


def ensure_event_loop():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html")


class AssetsHandler(tornado.web.StaticFileHandler):
    pass


class NoVNCHandler(tornado.web.StaticFileHandler):
    pass


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def open(self):
        self.session_id = uuid.uuid4().hex
        self.set_nodelay(True)
        WebSocketHandler.clients.add(self)
        mtda = self.application.settings['mtda']
        if mtda is not None:
            self.write_message(
                    {"session": {"id": self.session_id}}
            )
            self.write_message(
                    {"mtda-version": {"version": mtda.agent_version()}}
            )
            self.write_message(
                    {"console-output": {"output": mtda.console_dump()}}
            )
            self.write_message(
                    {"POWER": {"event": mtda.target_status(self.session_id)}}
            )
            status, _, _ = mtda.storage_status(self.session_id)
            self.write_message({"STORAGE": {"event": status}})
            if mtda.video is not None:
                fmt = mtda.video.format
                url = mtda.video.url(host=self.request.host)
                self.write_message({"video-info": {"format": fmt, "url": url}})

    def on_message(self, message):
        mtda = self.application.settings['mtda']
        if mtda is not None:
            sid = self.session_id
            if isinstance(message, bytes):
                mtda.debug(3, f"www.ws.on_message({len(message)} bytes, "
                              f"session={sid})")
                mtda.storage_write(message, session=sid)
            else:
                data = tornado.escape.json_decode(message)
                mtda.debug(3, f"www.ws.on_message({data})")
                if 'console-input' in data:
                    input = data['console-input']['input']
                    mtda.console_send(input, raw=False, session=sid)

    def on_close(self):
        WebSocketHandler.clients.remove(self)


class BaseHandler(tornado.web.RequestHandler):
    def result_as_json(self, result):
        response = {"result": result}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(response))


class KeyboardInputHandler(BaseHandler):
    def get(self):
        mtda = self.application.settings['mtda']
        result = ''
        input_key = self.get_argument("input", "")
        if mtda and mtda.keyboard:
            key_map = {
                "esc": mtda.keyboard.esc,
                "f1": mtda.keyboard.f1,
                "f2": mtda.keyboard.f2,
                "f3": mtda.keyboard.f3,
                "f4": mtda.keyboard.f4,
                "f5": mtda.keyboard.f5,
                "f6": mtda.keyboard.f6,
                "f7": mtda.keyboard.f7,
                "f8": mtda.keyboard.f8,
                "f9": mtda.keyboard.f9,
                "f10": mtda.keyboard.f10,
                "f11": mtda.keyboard.f11,
                "f12": mtda.keyboard.f12,
                "\b": mtda.keyboard.backspace,
                "    ": mtda.keyboard.tab,
                "caps": mtda.keyboard.capsLock,
                "\n": mtda.keyboard.enter,
                "left": mtda.keyboard.left,
                "right": mtda.keyboard.right,
                "up": mtda.keyboard.up,
                "down": mtda.keyboard.down,
            }
            if input_key in key_map:
                result = key_map[input_key]()
            else:
                result = mtda.keyboard.press(
                    input_key,
                    ctrl=self.get_argument('ctrl', 'false') == 'true',
                    shift=self.get_argument('shift', 'false') == 'true',
                    alt=self.get_argument('alt', 'false') == 'true',
                    meta=self.get_argument('meta', 'false') == 'true'
                )
        self.result_as_json({"result": result})


class PowerToggleHandler(BaseHandler):
    def get(self):
        mtda = self.application.settings['mtda']
        result = ''
        if mtda is not None:
            sid = self.get_argument('session')
            result = mtda.target_toggle(session=sid)
        self.result_as_json({"result": result})


class StorageFlushHandler(BaseHandler):
    def get(self):
        mtda = self.application.settings['mtda']
        result = ''
        if mtda is not None:
            size = self.get_argument('size')
            sid = self.get_argument('session')
            result = mtda.storage_flush(size=size, session=sid)
        self.result_as_json({"result": result})


class StorageOpenHandler(BaseHandler):
    def get(self):
        mtda = self.application.settings['mtda']
        result = ''
        if mtda is not None:
            from mtda.storage.datastream import LocalDataStream
            stream = LocalDataStream()
            sid = self.get_argument('session')
            result = mtda.storage_open(stream=stream, session=sid)
        self.result_as_json({"result": result})


class StorageCloseHandler(BaseHandler):
    def get(self):
        mtda = self.application.settings['mtda']
        result = ''
        if mtda is not None:
            sid = self.get_argument('session')
            result = mtda.storage_close(session=sid)
        self.result_as_json({"result": result})


class StorageToggleHandler(tornado.web.RequestHandler):
    def get(self):
        mtda = self.application.settings['mtda']
        result = ''
        if mtda is not None:
            sid = self.get_argument('session')
            status, _, _ = mtda.storage_status(session=sid)
            if status == CONSTS.STORAGE.ON_HOST:
                result = (
                        'TARGET'
                        if mtda.storage_to_target(session=sid)
                        else 'HOST'
                )
            elif status == CONSTS.STORAGE.ON_TARGET:
                result = (
                        'HOST'
                        if mtda.storage_to_host(session=sid)
                        else 'TARGET'
                )
        self.write(result)


class Service:
    def __init__(self, mtda):
        self.mtda = mtda
        self._host = CONSTS.DEFAULTS.WWW_HOST
        self._port = CONSTS.DEFAULTS.WWW_PORT
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.application = tornado.web.Application([
            (r"/", MainHandler),
            (r"/assets/(.*)", AssetsHandler, {
                "path": os.path.join(BASE_DIR, "assets")
            }),
            (r"/novnc/(.*)", NoVNCHandler, {
                "path": "/usr/share/novnc"
            }),
            (r"/mtda", WebSocketHandler),
            (r"/keyboard-input", KeyboardInputHandler),
            (r"/power-toggle", PowerToggleHandler),
            (r"/storage-close", StorageCloseHandler),
            (r"/storage-flush", StorageFlushHandler),
            (r"/storage-open", StorageOpenHandler),
            (r"/storage-toggle", StorageToggleHandler),
        ], mtda=mtda, debug=False)
        self.secret_key = secrets.token_hex(16)

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    def configure(self, conf):
        if 'host' in conf:
            self._host = conf['host']
        if 'port' in conf:
            self._port = int(conf['port'])

    async def run(self):
        ensure_event_loop()
        self.application.listen(self._port, self._host)
        self._loop = asyncio.get_running_loop()
        await asyncio.Event().wait()

    def start(self):
        thread = threading.Thread(
                target=lambda: asyncio.run(self.run()),
                daemon=True
        )
        thread.start()

    def stop(self):
        self.mtda.debug(3, "www.stop()")

        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

        self.mtda.debug(3, "www.stop: done")
        return None

    def _send_to_clients(self, message):
        for client in WebSocketHandler.clients:
            client.write_message(message)

    def notify(self, what, event):
        message = {what: {"event": event}}
        loop = tornado.ioloop.IOLoop.current()
        loop.add_callback(self._send_to_clients, message)

    def write(self, topic, data):
        message = {topic: {"output": data}}
        loop = tornado.ioloop.IOLoop.current()
        loop.add_callback(self._send_to_clients, message)
