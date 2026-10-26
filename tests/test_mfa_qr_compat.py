"""Regression tests for real Supabase authenticator QR representations."""

import pytest
from fastapi import HTTPException

from cloud.api import normalize_totp_qr_svg

SVG = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10" /></svg>'


@pytest.mark.parametrize(
    "input_qr",
    [
        SVG,
        '<?xml version="1.0" encoding="UTF-8"?>\n' + SVG,
        "data:image/svg+xml;utf-8," + SVG,
        "data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3C%2Fsvg%3E",
    ],
)
def test_compatible_valid_svg_formats(input_qr):
    assert normalize_totp_qr_svg(input_qr).lstrip().startswith(("<svg", "<?xml"))


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "",
        "not an image",
        "<html></html>",
        '<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg>&x;</svg>',
        "<svg><script>alert(1)</script></svg>",
        "data:text/html,<svg></svg>",
        pytest.param("X" * 100_001, id="oversized-qr"),
    ],
)
def test_unsafe_or_unrecognized_qr_fails_closed(bad):
    with pytest.raises(HTTPException) as error:
        normalize_totp_qr_svg(bad)
    assert error.value.status_code == 503
    assert "secret" not in str(error.value.detail).lower()


def test_enrollment_endpoint_accepts_xml_prefixed_svg(monkeypatch):
    import base64
    import json

    from fastapi.testclient import TestClient

    from cloud import api as service

    monkeypatch.setenv("QF_PROXY_SECRET", "proxy-test")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://test.pages.dev")
    monkeypatch.setenv("OWNER_USER_ID", "owner-id")

    def part(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    token = ".".join(
        (
            part({"alg": "HS256"}),
            part({"role": "authenticated", "sub": "owner-id", "aal": "aal1"}),
            "signature",
        )
    )

    class Reply:
        status_code = 200

        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def stub(method, path, **kwargs):
        if path == "/auth/v1/user":
            return Reply(
                {"id": "owner-id", "email_confirmed_at": "2026-01-01T00:00:00Z", "factors": []}
            )
        if path == "/auth/v1/factors":
            return Reply(
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "totp": {"qr_code": '<?xml version="1.0"?>\n' + SVG, "secret": "DO-NOT-EXPOSE"},
                }
            )
        raise AssertionError(f"Unexpected provider call: {method} {path}")

    monkeypatch.setattr(service, "sb_request", stub)
    with TestClient(service.app, base_url="https://render.invalid") as client:
        client.cookies.set("qf_access", token)
        response = client.post(
            "/api/auth/mfa/enroll",
            json={},
            headers={
                "x-qf-proxy-secret": "proxy-test",
                "origin": "https://test.pages.dev",
                "x-qf-action": "1",
            },
        )
    assert response.status_code == 200, response.text
    assert response.json()["qr_svg"].startswith("<?xml")
    assert "DO-NOT-EXPOSE" not in response.text
