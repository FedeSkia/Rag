from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

import jwt
from rag_app.config import CONFIG


class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request) -> str:
        creds: HTTPAuthorizationCredentials = await super().__call__(request)
        if not creds or not creds.scheme.lower() == "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        try:
            claims = jwt.decode(creds.credentials, CONFIG.JWT_SECRET, algorithms=[CONFIG.JWT_ALG])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")
        # attach claims to request for downstream handlers
        request.state.claims = claims
        return creds.credentials


def get_user_id(request: Request) -> str:
    claims = getattr(request.state, "claims", None)
    user_id = claims.get("sub") if claims else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No user in token")
    return user_id
