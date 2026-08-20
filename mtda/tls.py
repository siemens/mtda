# ---------------------------------------------------------------------------
# TLS channel helper for MTDA gRPC clients
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------
#
# Builds the gRPC channel used by mtda-cli, mtda-www and other MTDA client
# code to reach a (possibly remote) agent. When the [security] section
# enables TLS, the channel authenticates the server (and, if a client
# certificate/key pair is configured, itself to the server via mutual TLS)
# instead of connecting in the clear - see docs/hardening.rst.

import grpc
import grpc.aio


def _read(path):
    if path is None:
        return None
    with open(path, 'rb') as f:
        return f.read()


def build_channel(target, agent):
    """Return a gRPC channel to "target" (host:port), secured according to
    the "agent" configuration's [security] tls_* settings, or a plain
    insecure channel when TLS is not enabled (the default, matching
    MTDA's historical behavior on trusted networks)."""

    if not getattr(agent, 'tls_enabled', False):
        return grpc.insecure_channel(target)

    root_certificates = _read(getattr(agent, 'tls_ca', None))
    certificate_chain = _read(getattr(agent, 'tls_cert', None))
    private_key = _read(getattr(agent, 'tls_key', None))

    credentials = grpc.ssl_channel_credentials(
        root_certificates=root_certificates,
        private_key=private_key,
        certificate_chain=certificate_chain)

    options = ()
    server_name = getattr(agent, 'tls_server_name', None)
    if server_name:
        options = (('grpc.ssl_target_name_override', server_name),)

    return grpc.secure_channel(target, credentials, options=options)


def build_aio_channel(target, agent):
    """Same as build_channel(), but returns a grpc.aio channel for use in
    asyncio-based clients (e.g. mtda-www's WebConsole, which streams
    console/monitor events via grpc.aio so it can be awaited directly
    inside Tornado's event loop)."""

    if not getattr(agent, 'tls_enabled', False):
        return grpc.aio.insecure_channel(target)

    root_certificates = _read(getattr(agent, 'tls_ca', None))
    certificate_chain = _read(getattr(agent, 'tls_cert', None))
    private_key = _read(getattr(agent, 'tls_key', None))

    credentials = grpc.ssl_channel_credentials(
        root_certificates=root_certificates,
        private_key=private_key,
        certificate_chain=certificate_chain)

    options = ()
    server_name = getattr(agent, 'tls_server_name', None)
    if server_name:
        options = (('grpc.ssl_target_name_override', server_name),)

    return grpc.aio.secure_channel(target, credentials, options=options)


def build_server_credentials(agent):
    """Return grpc.ServerCredentials for the agent's own gRPC listener
    (mtda-service), or None when [security] server_tls is disabled (the
    default), in which case the caller should fall back to
    add_insecure_port - matching MTDA's historical behavior on trusted
    networks.

    Used when a reverse proxy (Traefik) and the agent run on separate
    nodes, so the hop between them is authenticated and encrypted too
    instead of relying on network trust alone. When "server_client_ca" is
    set, the proxy must present a client certificate signed by that CA
    (mutual TLS on this second hop) - this is what makes it safe for the
    agent to trust an identity header forwarded by the proxy from its own
    (separate) client-facing mTLS hop; see docs/hardening.rst."""

    if not getattr(agent, 'server_tls', False):
        return None

    private_key = _read(getattr(agent, 'server_key', None))
    certificate_chain = _read(getattr(agent, 'server_cert', None))
    if private_key is None or certificate_chain is None:
        raise ValueError(
            'server_tls is enabled but server_key/server_cert are not set')

    client_ca = _read(getattr(agent, 'server_client_ca', None))
    require_client_auth = bool(client_ca) and getattr(
        agent, 'server_require_client_cert', True)

    return grpc.ssl_server_credentials(
        [(private_key, certificate_chain)],
        root_certificates=client_ca,
        require_client_auth=require_client_auth)


def parse_remote(remote):
    """Parse a -r/--remote or $MTDA_REMOTE value into (host, port, tls).

    This lets a single value carry everything needed to reach an agent
    directly or through a TLS-terminating reverse proxy (e.g. Traefik),
    without having to edit a configuration file for one-off connections:

      host                  -> (host, None, False)
      host:port              -> (host, port, False)
      mtda://host[:port]     -> (host, port or None, False)
      mtdas://host[:port]    -> (host, port or None, True)

    "port" is None when not specified, so callers can fall back to their
    own default (e.g. the configured control port) instead of a value
    hardcoded here. The "mtdas://" scheme enables TLS the same way setting
    [security] tls = true in the configuration would, which is convenient
    for a one-off client connecting to an agent through a Traefik mTLS
    front-end (see docs/hardening.rst); certificate/key/CA paths still
    come from the configuration ([security] tls_ca/tls_cert/tls_key).
    Bracketed IPv6 literals (e.g. "[::1]:5556") are supported.
    """
    if remote is None:
        return remote, None, False

    tls = False
    value = remote
    if value.startswith('mtdas://'):
        tls = True
        value = value[len('mtdas://'):]
    elif value.startswith('mtda://'):
        value = value[len('mtda://'):]

    port = None
    host = value
    if value.startswith('['):
        # [ipv6-literal] or [ipv6-literal]:port
        end = value.find(']')
        if end != -1:
            host = value[1:end]
            rest = value[end + 1:]
            if rest.startswith(':') and rest[1:].isdigit():
                port = int(rest[1:])
    elif value.count(':') == 1:
        # plain "host:port" (bare IPv6 without brackets has more than one
        # colon and is left untouched, matching URL bracket conventions)
        candidate_host, _, candidate_port = value.partition(':')
        if candidate_port.isdigit():
            host = candidate_host
            port = int(candidate_port)

    return host, port, tls
