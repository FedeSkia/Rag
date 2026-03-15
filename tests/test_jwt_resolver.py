"""Tests for web_api/jwt_resolver.py."""
import time

import jwt
import pytest
from fastapi import FastAPI, Depends
from httpx import AsyncClient, ASGITransport

from rag_app.config import CONFIG
from rag_app.web_api.jwt_resolver import JWTBearer

app = FastAPI()


@app.get("/protected")
async def protected(user_id: str = Depends(JWTBearer())):
    return {"user_id": user_id}


def _make_token(sub: str = "user-123", exp_offset: int = 3600, **overrides) -> str:
    now = int(time.time())
    payload = {"sub": sub, "aud": "authenticated", "iat": now, "exp": now + exp_offset, **overrides}
    return jwt.encode(payload, CONFIG.JWT_SECRET, algorithm=CONFIG.JWT_ALG)


@pytest.mark.asyncio
async def test_valid_token():
    token = _make_token()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "user-123"


@pytest.mark.asyncio
async def test_expired_token():
    token = _make_token(exp_offset=-10)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_signature():
    payload = {"sub": "user-1", "aud": "authenticated", "iat": int(time.time()), "exp": int(time.time()) + 3600}
    token = jwt.encode(payload, "wrong-secret-key-that-is-long-enough", algorithm="HS256")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/protected")
    assert resp.status_code == 403  # FastAPI HTTPBearer returns 403 when no creds


@pytest.mark.asyncio
async def test_no_sub_in_token():
    now = int(time.time())
    payload = {"aud": "authenticated", "iat": now, "exp": now + 3600}
    token = jwt.encode(payload, CONFIG.JWT_SECRET, algorithm=CONFIG.JWT_ALG)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
