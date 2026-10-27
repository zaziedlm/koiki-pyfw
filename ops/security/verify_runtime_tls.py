"""Verify TLS trust and JWT behavior in the installed application environment."""

import datetime
import http.server
import importlib.metadata
import json
import pathlib
import socket
import ssl
import sys
import tempfile
import threading
import urllib.request

import certifi
import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def _write_fixture(directory, now):
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "KOIKI isolated TLS fixture")
    ])
    ca = (
        x509.CertificateBuilder()
        .subject_name(issuer)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=False,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=True, crl_sign=True,
                encipher_only=None, decipher_only=None,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )
    server = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost")
        ]))
        .issuer_name(issuer)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False
        )
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .sign(ca_key, hashes.SHA256())
    )
    (directory / "ca.pem").write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    (directory / "server.pem").write_bytes(
        server.public_bytes(serialization.Encoding.PEM)
    )
    (directory / "key.pem").write_bytes(server_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))


def _check_local_tls(results, now):
    with tempfile.TemporaryDirectory() as temporary:
        directory = pathlib.Path(temporary)
        _write_fixture(directory, now)
        server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.load_cert_chain(directory / "server.pem", directory / "key.pem")
        server.socket = server_context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        trusted = ssl.create_default_context(cafile=str(directory / "ca.pem"))
        cases = [
            ("fixture_trusted", trusted, "localhost", True),
            ("fixture_untrusted", ssl.create_default_context(), "localhost", False),
            ("fixture_hostname_mismatch", trusted, "wrong.invalid", False),
        ]
        try:
            for name, context, hostname, expected in cases:
                accepted = False
                try:
                    # Direct sockets keep proxy configuration out of local checks.
                    with socket.create_connection(
                        ("127.0.0.1", server.server_port), timeout=10
                    ) as connection:
                        with context.wrap_socket(connection, server_hostname=hostname):
                            accepted = True
                except ssl.SSLCertVerificationError:
                    pass
                if accepted != expected:
                    raise RuntimeError(f"Unexpected TLS verification result: {name}")
                results[name] = "pass"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


def main():
    results = {
        "python": sys.version,
        "openssl": ssl.OPENSSL_VERSION,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["certifi", "PyJWT", "cryptography", "starlette", "mako"]
        },
    }
    now = datetime.datetime.now(datetime.timezone.utc)
    _check_local_tls(results, now)
    for label, path in [
        ("system", "/etc/ssl/certs/ca-certificates.crt"),
        ("certifi", certifi.where()),
    ]:
        roots = ssl.create_default_context(cafile=path).get_ca_certs()
        if any("emsign ecc root ca - g3" in str(root.get("subject", "")).lower()
               for root in roots):
            raise RuntimeError(f"Affected emSign G3 root remains in {label}")
        results[label + "_affected_emsign_g3_root_absent"] = True
    with urllib.request.urlopen("https://pypi.org/simple/certifi/", timeout=30) as response:
        if response.status != 200:
            raise RuntimeError("Verified external TLS request failed")
        results["verified_external_tls_status"] = response.status

    secret = "isolated-security-verification-key-20261027"
    token = jwt.encode(
        {"sub": "fixture", "exp": int(now.timestamp()) - 3600},
        secret, algorithm="HS256",
    )
    options = {"verify_signature": False}
    original = options.copy()
    # This unverified decode only checks option mutation for a locally generated token.
    jwt.decode(token, options=options)
    if options != original:
        raise RuntimeError("PyJWT mutated the caller's options")
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        results["expired_jwt_rejected"] = True
    else:
        raise RuntimeError("Expired JWT was accepted")
    results["pyjwt_options_not_mutated"] = True
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
