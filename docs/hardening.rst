.. _hardening:

Hardening Guide
===============

By default, MTDA is designed for trusted lab/network environments: the
gRPC control channel is unauthenticated and unencrypted
(``grpc.insecure_channel``/``add_insecure_port``), and the "session"
identifier used for locking and idle-tracking is a client-supplied string
with no verification behind it (see ``mtda/session.py`` and
``Client._generate_session()`` in ``mtda/client.py``). Anyone able to reach
an agent's control port can send any ``mtda-session`` value they like,
including one already in use, and hijack that session's lock.

This guide describes how to put `Traefik`_ in front of MTDA to add real
client authentication (mutual TLS) end to end - from ``mtda-cli``/other
clients through Traefik to the agent - and bind MTDA's session identity to
a verified client certificate, plus general recommendations for reducing
the attack surface of an MTDA deployment.

Everything in this guide is **optional and off by default**: an
unhardened deployment keeps working exactly as before. Enable it when
agents are reachable from outside a fully trusted network.

.. contents::
   :local:

Threat model
------------

Without hardening, assume:

* Anyone with network access to an agent's gRPC port (``5556`` by default)
  can issue any command the agent exposes, with no authentication.
* Anyone can claim any session name, including one belonging to another
  user, and take over their console lock or storage/power ownership.
* Traffic (console output, storage images, credentials embedded in scripts,
  etc.) is sent in clear text over the network.

Hardening addresses these by:

1. Terminating mutual TLS (mTLS) at a reverse proxy (Traefik), so only
   clients presenting a certificate signed by a trusted CA can connect.
2. Deriving the MTDA session identity from that verified certificate
   instead of trusting the client-supplied session name.
3. Restricting network exposure of the agent itself (bind address, TLS on
   its own listener, and a firewall) so the proxy cannot be bypassed.

Deployment shapes
------------------

Two shapes are common, and matter for how much of this guide applies:

* **Single host**: Traefik (and possibly ``mtda-tv``) and the agent
  (``mtda-service``/``mtda-www``) run on the same machine. The
  Traefik-to-agent hop never leaves the machine, so binding the agent to
  ``127.0.0.1`` is enough to protect it.
* **Gateway + device-under-test nodes**: Traefik and ``mtda-tv`` run on one
  gateway machine, while each device-under-test has its own
  ``mtda-service``/``mtda-www`` on a separate node (mtda-tv's `Traefik
  (mtda-tv gateway)`_ integration is built around this shape). Here the
  Traefik-to-agent hop *does* cross the network, so it needs its own
  authentication and encryption - see `Securing the Traefik-to-agent hop`_
  below - in addition to firewalling (`Defense in depth`_).

Enforcing client-certificate authentication with Traefik
----------------------------------------------------------

Traefik terminates mTLS on a dedicated entry point and forwards traffic to
an agent's gRPC port. A sample dynamic configuration is provided in
``configs/traefik/dynamic-mtls.yml``; enable it from ``traefik.yml`` by
uncommenting the ``agents`` entry point and ``file`` provider (see
``configs/traefik/traefik.yml``).

1. **Create a CA and issue client certificates.** For a small/lab setup,
   a self-signed CA is enough::

       $ openssl req -x509 -newkey rsa:4096 -days 3650 -nodes \
           -keyout ca-key.pem -out ca.pem -subj "/CN=mtda-ca"

       # one certificate per user/client
       $ openssl req -newkey rsa:4096 -nodes \
           -keyout alice-key.pem -out alice.csr -subj "/CN=alice"
       $ openssl x509 -req -in alice.csr -CA ca.pem -CAkey ca-key.pem \
           -CAcreateserial -out alice.pem -days 365

   Distribute ``alice.pem``/``alice-key.pem`` to the user, and keep
   ``ca-key.pem`` offline once the CA is established. For anything beyond
   a small team, use a proper internal CA/PKI instead of hand-rolled
   certificates.

2. **Configure Traefik's server certificate and CA** in
   ``configs/traefik/dynamic-mtls.yml`` (``tls.certificates`` and
   ``tls.options.mtls.clientAuth.caFiles``), and point the router's
   ``rule`` and service ``url`` at your agent's hostname and gRPC port.

3. **Enable the ``agents`` entry point and ``file`` provider** in
   ``traefik.yml`` (see the commented block already present there), then
   restart Traefik.

Running Traefik in production
------------------------------

Once you've validated the setup, move it out of an ad-hoc working
directory into a permanent, root-owned location so it survives reboots
and isn't tied to a particular user's home directory:

1. **Store certificates and keys under a dedicated, root-owned
   directory**, e.g. ``/etc/mtda/certs/``::

       $ sudo mkdir -p /etc/mtda/certs
       $ sudo cp ca.pem traefik.pem traefik-key.pem /etc/mtda/certs/
       $ sudo chown root:root /etc/mtda/certs/*
       $ sudo chmod 644 /etc/mtda/certs/ca.pem /etc/mtda/certs/traefik.pem
       $ sudo chmod 600 /etc/mtda/certs/traefik-key.pem

   Client certificates (e.g. ``alice.pem``/``alice-key.pem``) should be
   distributed to each user's own machine rather than kept on the
   Traefik host. Keep the CA private key (``ca-key.pem``) offline once
   the CA is established; only keep it on the host temporarily if you
   need to issue certificates locally, and remove it afterwards.

2. **Move the Traefik configuration** (``traefik.yml``, ``dynamic/``,
   ``docker-compose.yml``) to a permanent location such as
   ``/etc/mtda/traefik/``, and point the compose file's certificate
   volume mount at ``/etc/mtda/certs`` instead of a relative path.

3. **Run Traefik under systemd** instead of manually invoking
   ``docker compose up -d``, so it starts automatically on boot and
   restarts on failure::

       $ sudo tee /etc/systemd/system/mtda-traefik.service <<'EOF'
       [Unit]
       Description=Traefik reverse proxy for MTDA (mTLS hardening front-end)
       After=network-online.target docker.service
       Wants=network-online.target
       Requires=docker.service

       [Service]
       Type=oneshot
       RemainAfterExit=yes
       WorkingDirectory=/etc/mtda/traefik
       ExecStart=/usr/bin/docker-compose up -d
       ExecStop=/usr/bin/docker-compose down
       ExecReload=/usr/bin/docker-compose up -d --force-recreate
       TimeoutStartSec=60

       [Install]
       WantedBy=multi-user.target
       EOF
       $ sudo systemctl daemon-reload
       $ sudo systemctl enable --now mtda-traefik.service

   Docker's own ``restart: unless-stopped`` policy on the container
   keeps it running across Docker restarts; the systemd unit on top
   ensures the *stack* comes up automatically after a host reboot and
   gives you the usual ``systemctl status``/``journalctl -u`` tooling.

Connecting mtda-cli (and other clients) through Traefik
---------------------------------------------------------

``mtda-cli``, ``mtda.client.Client`` and the remote console/monitor
streams all support reaching an agent through a TLS/mTLS front-end - no
external tooling required. Two ways to enable it:

* **One-off, without touching a config file**: pass a ``mtdas://`` URL to
  ``-r``/``--remote`` (or ``$MTDA_REMOTE``), which both selects TLS and
  lets you specify a non-default port (e.g. Traefik's ``agents`` entry
  point)::

      $ mtda-cli -r mtdas://gateway.example.com:8443 status

  Accepted ``-r``/``$MTDA_REMOTE`` forms: ``host``, ``host:port``,
  ``mtda://host[:port]`` (plaintext, explicit) and ``mtdas://host[:port]``
  (TLS). Bracketed IPv6 literals (``[::1]:8443``) are supported. An
  explicit port here always overrides the ``[remote] control`` setting
  from a configuration file.

* **Persistent, via configuration** (``~/.mtda/config`` or
  ``/etc/mtda/config.d/*.conf``, see :ref:`config`)::

      [remote]
      host = gateway.example.com
      control = 8443

      [security]
      tls = true
      tls_ca = /etc/mtda/tls/ca.pem
      tls_cert = /etc/mtda/tls/alice.pem
      tls_key = /etc/mtda/tls/alice-key.pem

  ``tls_ca`` verifies Traefik's server certificate; ``tls_cert``/``tls_key``
  present the client's own certificate for mutual TLS. Set
  ``tls_server_name`` if you connect by IP or through a tunnel under a
  different name than the certificate's Subject/SAN.

Connecting from a browser (mtda-www through Traefik)
-----------------------------------------------------

The same client-certificate model applies to Traefik routes fronting
``mtda-www``/``mtda-tv``, not just the gRPC control channel - useful when
you want browser users to authenticate the same way as ``mtda-cli``
users. Add an HTTPS entry point in ``traefik.yml`` (e.g. ``:8443``)
alongside the plain ``web`` one, and a ``tls.options`` block in your
dynamic configuration requiring client certificates
(``clientAuthType: RequireAndVerifyClientCert``), the same way
``dynamic-mtls.yml`` does for the gRPC hop. Give that TLS options block
the name ``default`` (rather than a custom name) if your routers match
on ``PathPrefix`` instead of ``Host`` - Traefik selects a *named* TLS
options block by SNI, which only works with ``Host``-based rules;
``default`` is applied regardless of SNI/routing.

.. important::
   A Traefik router needs its own ``tls`` section (even an empty ``{}``)
   to be reachable over a TLS entry point at all - and, conversely, a
   router carrying ``tls`` is then excluded from any plain entry point.
   One router cannot serve both, so keep (or add) a **separate router
   per entry point** for anything you want reachable both ways, each
   restricted to its own ``entryPoints``, both pointing at the same
   ``service``. If you use ``[gateway]`` (mtda-tv's own reverse-proxy
   integration - see `Traefik (mtda-tv gateway)`_) alongside this guide,
   set ``tls_entry_point = websecure`` in ``20-gateway.conf`` and mtda-tv
   generates this second, TLS-only router for every discovered agent
   automatically; leave it unset to keep gateway routes plain-only.

To use this from a browser, issue each user a certificate/key pair from
your CA and bundle it as a PKCS#12 file (including the CA certificate so
the OS/browser can validate the chain)::

    $ openssl pkcs12 -export -out alice.p12 \
        -inkey alice-key.pem -in alice.pem -certfile ca.pem

Import ``alice.p12`` into the browser's/OS's certificate store (e.g.
double-clicking it on macOS imports it into Keychain Access), and trust
the CA that issued Traefik's *server* certificate if it isn't already a
public one. Browsing to the HTTPS entry point then prompts for a client
certificate; the browser presents the imported identity, and a request
with no certificate, or one from an untrusted CA, is rejected at the TLS
handshake before any application code runs. Exact steps vary by browser
and OS - consult their documentation for importing PKCS#12 client
certificates and trusting a custom CA.

Binding session identity to the verified certificate
-----------------------------------------------------

Once mTLS is enforced, enable the agent-side ``[security]`` settings (see
``configs/30-security.conf`` and :ref:`config`)::

    [security]
    bind = 127.0.0.1
    trust_proxy_identity = true
    # identity_header = x-forwarded-tls-client-cert-info

With ``trust_proxy_identity`` enabled, the agent ignores any
``mtda-session`` metadata sent by the client and instead reads the Subject
CN forwarded by Traefik's ``passTLSClientCert`` middleware (configured in
``dynamic-mtls.yml``), using it as the session name (prefixed with
``cert:``, e.g. ``cert:alice``). Session locking and idle-tracking then
reflect a cryptographically verified identity: a client cannot claim
another user's session, since doing so would require that user's private
key.

This guarantee only holds while the header truly originates from your
Traefik instance - see the next two sections.

Securing the Traefik-to-agent hop
-----------------------------------

In the gateway + device-under-test-nodes shape, the identity header
travels over the network between Traefik and the agent. Left unencrypted
and unauthenticated, anyone able to reach the agent directly could forge
that header and impersonate any user, which would defeat the entire point
of ``trust_proxy_identity``. Secure this hop with the agent's own
server-side TLS support::

    [security]
    server_tls = true
    server_cert = /etc/mtda/tls/agent.pem
    server_key = /etc/mtda/tls/agent-key.pem
    server_client_ca = /etc/mtda/tls/ca.pem
    server_require_client_cert = true

``server_client_ca`` + ``server_require_client_cert`` make this a second,
independent mTLS hop: the agent only accepts connections presenting a
client certificate signed by that CA, which should be issued to Traefik
itself (not to end users). Configure the matching Traefik-side
``serversTransport`` (Traefik's client certificate for this hop, and the
CA verifying the agent's server certificate) in
``configs/traefik/dynamic-mtls.yml``; the service URL there becomes
``https://<agent>:5556`` instead of a plaintext scheme once this is done.

When Traefik and the agent share the same host and ``bind`` is
loopback-only, this second hop never leaves the machine and
``server_tls`` may reasonably be left disabled - the choice is a
risk/deployment call, not a hard requirement in that specific case.

.. important::
   ``mtda-tv`` (agent polling/snapshots for the grid dashboard) and
   ``mtda-www`` (the console/monitor streaming tabs) are themselves gRPC
   clients of the agent, separate from Traefik. Once ``server_tls`` is
   enabled on an agent, both need the matching client-side ``[security]``
   settings (``tls = true``, ``tls_ca``, and a client certificate if
   ``server_require_client_cert`` is set) in their own configuration, or
   they will fail to reach that agent - ``mtda-tv``'s tile for it will
   stop updating, and ``mtda-www``'s console/monitor tabs will stop
   streaming. ``mtda-tv`` reads these settings from the same
   ``[security]`` section as ``mtda-cli`` (``config.d`` fragments are
   shared), applied uniformly to every agent it polls; ``mtda-www``
   reuses whatever ``[security]`` client settings its own local
   ``mtda.conf`` already carries to reach its agent.

Defense in depth
-----------------

The identity-forwarding protection above only holds if the agent truly
cannot be reached other than through the proxy. Treat the following as
required, not optional, especially in the gateway + device-under-test
shape:

* **Set** ``[security] bind`` **to a loopback or private/management
  address** on each node running ``mtda-service`` (e.g. ``127.0.0.1`` if
  Traefik runs on the same host, or that node's management interface
  address otherwise) so the gRPC port is not reachable from the same
  network segment as end-user clients.

* **Firewall every node running** ``mtda-service`` **and** ``mtda-www``
  **to only accept connections from the gateway** (the Traefik host),
  independent of ``bind`` - defense in depth in case of a misconfigured
  bind address or a service restart picking up the wrong interface. On a
  ``nftables``-based node::

      $ sudo nft add table inet mtda
      $ sudo nft add chain inet mtda input \
          '{ type filter hook input priority 0; policy drop; }'
      $ sudo nft add rule inet mtda input iif lo accept
      $ sudo nft add rule inet mtda input ct state established,related accept
      $ sudo nft add rule inet mtda input ip saddr <gateway-ip> tcp dport \
          { 5556, 5000 } accept
      $ sudo nft add rule inet mtda input ip saddr <gateway-ip> tcp dport \
          22 accept

  (adjust ``5556``/``5000`` for the control and ``mtda-www`` ports; drop
  the ``22`` rule if you manage the node through some other trusted
  channel). An equivalent ``iptables``/``ufw`` ruleset works just as well
  - the key point is a default-deny policy on those ports with an
  allowlist limited to the gateway's address, not the rule syntax:

  .. code-block:: text

      # iptables equivalent
      iptables -P INPUT DROP
      iptables -A INPUT -i lo -j ACCEPT
      iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
      iptables -A INPUT -s <gateway-ip> -p tcp -m multiport \
          --dports 5556,5000 -j ACCEPT

      # ufw equivalent
      ufw default deny incoming
      ufw allow from <gateway-ip> to any port 5556,5000 proto tcp

* **Do not expose the Traefik dashboard** (``api.insecure``) in anything
  resembling production; it is commented out by default in the sample
  configs for that reason.

* **Rotate and revoke client certificates** the same way you would any
  other credential. Traefik's ``clientAuth`` does not check a CRL/OCSP
  responder out of the box; if certificate revocation matters for your
  deployment, look at Traefik's plugin ecosystem or terminate mTLS with a
  proxy that supports it natively.

* **Keep CA private keys offline** once issued; anyone holding one can
  mint a certificate for any identity, defeating the whole scheme. Use a
  separate CA (or at least separate signing keys) for client-facing
  certificates versus the Traefik/agent hop's certificates so compromising
  one does not automatically grant access on the other hop.

* **Apply the same treatment to** ``mtda-www`` **and** ``mtda-tv``: they
  are separate HTTP services (not covered by the gRPC ``[security]``
  section above) and should either sit behind the same reverse proxy with
  their own authentication, or be bound to a private/loopback interface
  (``[www] host``) and firewalled the same way as the control port.

* **Patch and pin Traefik and MTDA versions**; treat the reverse proxy as
  part of your security boundary and keep it updated like any other
  Internet/network-facing service.

Systemd service hardening
--------------------------

If you package/run ``mtda-service`` under systemd, consider adding
sandboxing directives to its unit (adjust as needed for hardware access
requirements, since MTDA typically needs access to serial/USB/GPIO
devices)::

    [Service]
    NoNewPrivileges=true
    ProtectSystem=strict
    ProtectHome=true
    PrivateTmp=true
    ReadWritePaths=/var/log /var/run

Test thoroughly after adding these, since overly strict sandboxing can
break access to the hardware devices MTDA manages.

Summary checklist
------------------

* [ ] Reverse proxy (Traefik) terminates mTLS in front of clients.
* [ ] ``mtda-cli``/clients connect via ``mtdas://`` or the client-side
      ``[security] tls_*`` settings instead of an unauthenticated channel.
* [ ] ``[security] bind`` restricts each agent's gRPC port to a
      loopback/private address.
* [ ] ``[security] trust_proxy_identity`` is enabled, binding sessions to
      verified client certificates instead of client-supplied names.
* [ ] When Traefik and the agent are on separate nodes,
      ``[security] server_tls``/``server_client_ca`` secure that hop too.
* [ ] Every node running ``mtda-service``/``mtda-www`` is firewalled to
      only accept connections from the gateway, independent of ``bind``.
* [ ] CA private keys are offline; certificates are issued and revoked
      like any other credential.
* [ ] The Traefik dashboard/API is disabled or itself protected.
* [ ] ``mtda-www``/``mtda-tv`` are bound to a private interface, firewalled,
      or sit behind the same authenticated proxy.

.. _Traefik: https://traefik.io/
.. _Traefik (mtda-tv gateway): integration.html#traefik-mtda-tv-gateway
