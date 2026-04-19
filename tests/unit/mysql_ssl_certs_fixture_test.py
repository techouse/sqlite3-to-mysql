from pathlib import Path

import pytest

from tests.conftest import (
    MySQLSSLCerts,
    _mysql_ssl_certs_from_environment,
    _mysql_ssl_certs_from_home,
)


def _write_ssl_cert_files(directory: Path) -> MySQLSSLCerts:
    ca = directory / "ca.pem"
    client_cert = directory / "client-cert.pem"
    client_key = directory / "client-key.pem"
    for cert_path in (ca, client_cert, client_key):
        cert_path.write_text("fake")

    return MySQLSSLCerts(
        ca=str(ca.resolve()),
        client_cert=str(client_cert.resolve()),
        client_key=str(client_key.resolve()),
    )


def test_mysql_ssl_certs_from_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    certs = _write_ssl_cert_files(tmp_path)
    monkeypatch.setenv("MYSQL_SSL_CA", certs.ca)
    monkeypatch.setenv("MYSQL_SSL_CERT", certs.client_cert)
    monkeypatch.setenv("MYSQL_SSL_KEY", certs.client_key)

    assert _mysql_ssl_certs_from_environment() == certs


def test_mysql_ssl_certs_from_environment_requires_all_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MYSQL_SSL_CA", str(tmp_path / "ca.pem"))

    with pytest.raises(pytest.fail.Exception, match="must be set together"):
        _mysql_ssl_certs_from_environment()


def test_mysql_ssl_certs_from_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    certs = _write_ssl_cert_files(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert _mysql_ssl_certs_from_home() == certs
