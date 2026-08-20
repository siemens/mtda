# Security Policy

## Security Considerations

MTDA (Multi-Tenant Device Access) is intended for use in **trusted and controlled environments**, such as laboratory, development, validation, and test infrastructure.

MTDA is **not designed to be exposed directly to untrusted networks or the public Internet**.

MTDA provides mechanisms that can give remote users significant control over an attached test device, including access to device consoles, USB devices, and power control. Consequently, access to an MTDA instance should be considered equivalent to privileged access to the associated test equipment.

### Security assumptions

MTDA assumes that the deployment environment provides appropriate security controls, including as applicable:

* Network isolation and access control
* Authentication and authorization
* Protection of the MTDA host itself
* Physical security of the MTDA hardware and attached test equipment
* Appropriate protection of credentials and configuration data

MTDA does not, by itself, provide a complete security boundary for an untrusted environment.

Users deploying MTDA in environments containing sensitive equipment, networks, credentials, or data should independently assess whether the security controls provided by their deployment are appropriate for their intended use.

### Optional hardening

MTDA optionally supports client-certificate authentication and TLS encryption for its gRPC control channel and web interface, typically enforced by a reverse proxy (e.g. Traefik) placed in front of MTDA. This is opt-in and disabled by default. See `docs/hardening.rst` for the threat model, deployment guidance, and configuration details.

### Vulnerability reporting

If you believe you have found a security vulnerability in MTDA, please report it privately to the project maintainers rather than opening a public GitHub issue.

Please include enough information to reproduce the issue, including the affected MTDA version and, where relevant, the configuration and deployment environment.

The maintainers will assess reported vulnerabilities and determine the appropriate remediation and disclosure process.

### Scope

This security policy describes the intended security model of MTDA. It does not constitute a security certification or guarantee that MTDA is free from security vulnerabilities.

MTDA has not been designed or assessed as a security boundary for hostile or untrusted environments.
