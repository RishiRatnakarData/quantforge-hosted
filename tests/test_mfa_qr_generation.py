"""Provider-independent MFA QR generation tests. No network or real secrets."""

import base64
import json
from xml.etree import ElementTree as ET

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from cloud import api as service

URI = "otpauth://totp/QuantForge%3AOwner?secret=JBSWY3DPEHPK3PXP&issuer=QuantForge"
FACTOR_ID = "11111111-1111-4111-8111-111111111111"


def test_svg_rendered_from_uri_ignores_broken_provider_qr():
    svg = service.generate_totp_qr_svg({"uri": URI, "qr_code": "invalid provider image"})
    assert ET.fromstring(svg).tag == "{http://www.w3.org/2000/svg}svg"
    assert "JBSWY3DPEHPK3PXP" not in svg
    assert "<path" in svg


def test_enrollment_uses_secret_when_provider_uri_is_missing():
    svg = service.generate_totp_qr_svg({"secret": "JBSWY3DPEHPK3PXP", "qr_code": ""})
    assert ET.fromstring(svg).tag == "{http://www.w3.org/2000/svg}svg"


@pytest.mark.parametrize(
    "uri",
    [
        "https://attacker.invalid/qr",
        "otpauth://hotp/Label?secret=JBSWY3DPEHPK3PXP",
        "otpauth://totp/Label?secret=BAD!",
        "otpauth://totp/Label?issuer=QuantForge",
        "otpauth://totp/Label?secret=JBSWY3DPEHPK3PXP#fragment",
    ],
)
def test_invalid_uri_rejected_without_leaking(uri):
    with pytest.raises(HTTPException) as exc:
        service.generate_totp_qr_svg({"uri": uri})
    assert exc.value.status_code == 503
    assert "JBSWY3DPEHPK3PXP" not in str(exc.value.detail)


def test_live_api_shape_with_invalid_provider_svg(monkeypatch):
    monkeypatch.setenv("QF_PROXY_SECRET", "test-proxy")
    monkeypatch.setenv("PUBLIC_SITE_ORIGIN", "https://test.pages.dev")
    monkeypatch.setenv("OWNER_USER_ID", "owner-id")

    def pack(value):
        return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")

    token = ".".join(
        (
            pack({"alg": "HS256"}),
            pack({"role": "authenticated", "sub": "owner-id", "aal": "aal1"}),
            "sig",
        )
    )

    class Reply:
        status_code = 200

        def __init__(self, obj):
            self.obj = obj

        def json(self):
            return self.obj

    def stub(method, path, **kwargs):
        if path == "/auth/v1/user":
            return Reply(
                {"id": "owner-id", "email_confirmed_at": "2026-01-01T00:00:00Z", "factors": []}
            )
        if path == "/auth/v1/factors":
            return Reply(
                {
                    "id": FACTOR_ID,
                    "totp": {
                        "uri": URI,
                        "secret": "JBSWY3DPEHPK3PXP",
                        "qr_code": "not an SVG; should be ignored",
                    },
                }
            )
        raise AssertionError("Unexpected test provider route")

    monkeypatch.setattr(service, "sb_request", stub)
    with TestClient(service.app, base_url="https://render.invalid") as client:
        client.cookies.set("qf_access", token)
        response = client.post(
            "/api/auth/mfa/enroll",
            json={},
            headers={
                "x-qf-proxy-secret": "test-proxy",
                "origin": "https://test.pages.dev",
                "x-qf-action": "1",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["factor_id"] == FACTOR_ID
    assert ET.fromstring(data["qr_svg"]).tag == "{http://www.w3.org/2000/svg}svg"
    assert "secret" not in data
    assert URI not in response.text
