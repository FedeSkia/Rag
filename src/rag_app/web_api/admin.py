import logging
import time

import httpx
import jwt
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
from rag_app.config import CONFIG

admin_router = APIRouter(prefix="/admin")


def _mint_service_jwt() -> str:
    """Create a short-lived service-role JWT for GoTrue admin endpoints."""
    now = int(time.time())
    payload = {
        "sub": "admin-cli",
        "role": "service_role",  # must be allowed by GOTRUE_JWT_ADMIN_ROLES
        "aud": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(payload, CONFIG.JWT_SECRET, algorithm=CONFIG.JWT_ALG)


@admin_router.delete("/delete_user")
async def delete_user_admin(user_id: str):
    """Admin: delete a user in local GoTrue via /admin/users/{id}.
    Requires that CONFIG.JWT_SECRET matches GoTrue's signing secret
    and that `service_role` is included in GOTRUE_JWT_ADMIN_ROLES.
    """
    admin_jwt = _mint_service_jwt()
    url = f"{CONFIG.GOTRUE_URL}/admin/users/{user_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.delete(url, headers={
            "Authorization": f"Bearer {admin_jwt}",
        })
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"status": "deleted", "user_id": user_id}


class CreateUser(BaseModel):
    email: str
    password: str


@admin_router.post("/create_user")
async def create_user_admin(req: CreateUser):
    async with httpx.AsyncClient(base_url=CONFIG.GOTRUE_URL, timeout=10) as client:
        resp = await client.post(
            "/signup",
            json=req.model_dump(),
            headers={"Accept": "application/json"},
        )

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    # GoTrue returns the user/session payload; return or shape as you like
    return {"status": "created", "gotrue": resp.json()}
