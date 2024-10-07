# ---------------------------------------------------------------------------
# Web service for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2024 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

from flask import Flask, render_template, request, session, send_from_directory
from flask_socketio import SocketIO
from urllib.parse import urlparse

import secrets
import threading
import uuid

import mtda.constants as CONSTS

app = Flask("mtda")
app.config["mtda"] = None
socket = SocketIO(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/assets/<path:path>')
def assets_dir(path):
    return send_from_directory('assets', path)


@app.route('/novnc/<path:path>')
def novnc_dir(path):
    return send_from_directory('/usr/share/novnc', path)


@socket.on("connect", namespace="/mtda")
def connect():
    session['id'] = uuid.uuid4().hex
    mtda = app.config['mtda']
    if mtda is not None:
        socket.emit("session", {"id": session['id']}, namespace="/mtda")

        version = mtda.agent_version()
        socket.emit("mtda-version", {"version": version}, namespace="/mtda")

        data = mtda.console_dump()
        socket.emit("console-output", {"output": data}, namespace="/mtda")

        power = mtda.target_status(session['id'])
        socket.emit("power-event", {"event": power}, namespace="/mtda")

        status, _, _ = mtda.storage_status(session['id'])
        socket.emit("storage-event", {"event": status}, namespace="/mtda")

        if mtda.video is not None:
            fmt = mtda.video.format
            url = urlparse(request.base_url)
            url = mtda.video.url(host=url.hostname)
            info = {"format": fmt, "url": url}
            socket.emit("video-info", info, namespace="/mtda")


@socket.on("console-input", namespace="/mtda")
def console_input(data):
    sid = session_id()
    mtda = app.config['mtda']
    if mtda is not None:
        mtda.console_send(data['input'], raw=False, session=sid)


@app.route('/keyboard-input')
def keyboard_input():
    mtda = app.config['mtda']
    map = {
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
    if mtda is not None and mtda.keyboard is not None:
        input = request.args.get('input', '', type=str)
        if len(input) > 1:
            if input in map:
                map[input]()
        else:
            mtda.keyboard.press(
                input,
                ctrl=request.args.get('ctrl', False, type=lambda s: s == 'true'),
                shift=request.args.get('shift', False, type=lambda s: s == 'true'),
                alt=request.args.get('alt', False, type=lambda s: s == 'true'),
                meta=request.args.get('meta', False, type=lambda s: s == 'true')
            )
    return ''


@app.route('/power-toggle')
def power_toggle():
    sid = request.args.get('session')
    mtda = app.config['mtda']
    if mtda is not None:
        return mtda.target_toggle(session=sid)
    return ''


@app.route('/storage-toggle')
def storage_toggle():
    sid = request.args.get('session')
    mtda = app.config['mtda']
    if mtda is not None:
        status, _, _ = mtda.storage_status(session=sid)
        if status == CONSTS.STORAGE.ON_HOST:
            return 'TARGET' if mtda.storage_to_target(session=sid) else 'HOST'
        elif status == CONSTS.STORAGE.ON_TARGET:
            return 'HOST' if mtda.storage_to_host(session=sid) else 'TARGET'
        return status
    return ''


@app.route('/storage-open')
def storage_open():
    sid = request.args.get('session')
    mtda = app.config['mtda']
    if mtda is not None:
        mtda.storage_open(session=sid)
    return ''


@socket.on("storage-close", namespace="/mtda")
def storage_close(data):
    sid = request.args.get('session')
    mtda = app.config['mtda']
    if mtda is not None:
        mtda.storage_close(sid)
        mtda.storage_to_target(sid)
    return ''


@socket.on("storage-write", namespace="/mtda")
def storage_write(data):
    sid = session_id()
    mtda = app.config['mtda']
    if mtda is not None:
        data = data['data']
        mtda.storage_write(data, sid)
    return ''


def session_id():
    sid = None
    if 'id' in session:
        sid = session['id']
    return sid


class Service:
    def __init__(self, mtda):
        self.mtda = mtda
        self._host = CONSTS.DEFAULTS.WWW_HOST
        self._port = CONSTS.DEFAULTS.WWW_PORT
        app.config['SECRET_KEY'] = secrets.token_hex(16)
        app.config['mtda'] = mtda

    def configure(self, conf):
        if 'host' in conf:
            self._host = conf['host']
        if 'port' in conf:
            self._port = int(conf['port'])

    @property
    def host(self):
        return self._host

    def notify(self, what, event):
        if what == CONSTS.EVENTS.POWER:
            socket.emit("power-event", {"event": event}, namespace="/mtda")
        elif what == CONSTS.EVENTS.SESSION:
            socket.emit("session-event", {"event": event}, namespace="/mtda")
        elif what == CONSTS.EVENTS.STORAGE:
            socket.emit("storage-event", {"event": event}, namespace="/mtda")

    @property
    def port(self):
        return self._port

    def run(self):
        return socket.run(app, debug=False, use_reloader=False,
                          port=self._port, host=self._host)

    def start(self):
        self._thread = threading.Thread(target=self.run)
        return self._thread.start()

    def stop(self):
        socket.stop()

    def write(self, topic, data):
        if topic == CONSTS.CHANNEL.CONSOLE:
            socket.emit("console-output", {"output": data}, namespace="/mtda")
