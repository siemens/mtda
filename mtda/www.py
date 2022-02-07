# ---------------------------------------------------------------------------
# Web service for MTDA
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2022 Siemens Digital Industries Software
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

from flask import Flask, render_template, session
from flask_socketio import SocketIO
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


@socket.on("connect", namespace="/mtda")
def connect():
    session['id'] = uuid.uuid4().hex
    mtda = app.config['mtda']
    if mtda is not None:
        data = mtda.console_dump()
        socket.emit("console-output", {"output": data}, namespace="/mtda")


@socket.on("console-input", namespace="/mtda")
def console_input(data):
    sid = session_id()
    mtda = app.config['mtda']
    if mtda is not None:
        mtda.console_send(data['input'], raw=False, session=sid)


@app.route('/power-toggle')
def power_toggle():
    sid = session_id()
    mtda = app.config['mtda']
    if mtda is not None:
        return mtda.target_toggle(session=sid)
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
