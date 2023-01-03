// --------------------------------------------------------------------------
// Load VNC video stream
// --------------------------------------------------------------------------
//
// This software is a part of MTDA.
// Copyright (C) 2023 Siemens Digital Industries Software
//
// --------------------------------------------------------------------------
// SPDX-License-Identifier: MIT
// --------------------------------------------------------------------------

import * as WebUtil from '/novnc/app/webutil.js';
import RFB from '/novnc/core/rfb.js';

var rfb;
var desktopName;

function updateDesktopName(e) {
    desktopName = e.detail.name;
}

function status(text, color) {
    document.getElementById('vnc_status').innerHTML = '<span style="color: ' + color + ';"><b>' + text + '</b></span>';
}

function connected(e) {
    status("Video", "green");
}

function disconnected(e) {
    if (e.detail.clean) {
        status("Disconnected", "red");
    } else {
        status("Error", "red");
    }
}

WebUtil.init_logging(WebUtil.getConfigVar('logging', 'warn'));
var host = WebUtil.getConfigVar('host', window.location.hostname);
var port = 5901
var password = ''
var path = WebUtil.getConfigVar('path', 'websockify');

// If a token variable is passed in, set the parameter in a cookie.
// This is used by nova-novncproxy.
var token = WebUtil.getConfigVar('token', null);
if (token) {
    // if token is already present in the path we should use it
    path = WebUtil.injectParamIfMissing(path, "token", token);

    WebUtil.createCookie('token', token, 1)
}

export function vnc_load() {

    status("Connecting", "orange");

    if ((!host) || (!port)) {
        status('Must specify host and port in URL', 'error');
    }

    var url;

    if (WebUtil.getConfigVar('encrypt',
                             (window.location.protocol === "https:"))) {
        url = 'wss';
    } else {
        url = 'ws';
    }

    url += '://' + host;
    if(port) {
        url += ':' + port;
    }
    url += '/' + path;

    rfb = new RFB(document.getElementById('video'), url,
                  { repeaterID: WebUtil.getConfigVar('repeaterID', ''),
                    shared: WebUtil.getConfigVar('shared', true),
                    credentials: { password: password } });
    rfb.viewOnly = WebUtil.getConfigVar('view_only', false);
    rfb.addEventListener("connect",  connected);
    rfb.addEventListener("disconnect", disconnected);
    rfb.addEventListener("desktopname", updateDesktopName);
    rfb.scaleViewport = WebUtil.getConfigVar('scale', true);
    rfb.resizeSession = WebUtil.getConfigVar('resize', false);
}
