"""Tests for web_api/admin.py — _mint_service_jwt logic."""
import time

import jwt

from rag_app.config import CONFIG
from rag_app.web_api.admin import _mint_service_jwt


class TestMintServiceJwt:
    def test_decodable(self):
        token = _mint_service_jwt()
        claims = jwt.decode(token, CONFIG.JWT_SECRET, algorithms=[CONFIG.JWT_ALG], audience="authenticated")
        assert claims["role"] == "service_role"
        assert claims["sub"] == "admin-cli"

    def test_expiry_is_future(self):
        token = _mint_service_jwt()
        claims = jwt.decode(token, CONFIG.JWT_SECRET, algorithms=[CONFIG.JWT_ALG], audience="authenticated")
        assert claims["exp"] > int(time.time())

    def test_audience(self):
        token = _mint_service_jwt()
        claims = jwt.decode(token, CONFIG.JWT_SECRET, algorithms=[CONFIG.JWT_ALG], audience="authenticated")
        assert claims["aud"] == "authenticated"
