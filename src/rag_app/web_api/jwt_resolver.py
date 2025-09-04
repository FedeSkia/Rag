import logging

import jwt
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from rag_app.config import CONFIG

logger = logging.getLogger(__name__)


class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request) -> str:
        creds: HTTPAuthorizationCredentials = await super().__call__(request)
        if not creds or not creds.scheme.lower() == "bearer":
            logger.debug("No bearer token in request headers: %s", dict(request.headers))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        try:
            claims = jwt.decode(creds.credentials, CONFIG.JWT_SECRET, algorithms=[CONFIG.JWT_ALG],
                                options={"verify_signature": False})
            # claims = jwt.decode(
            #     token,
            #     CONFIG.JWT_SECRET,
            #     algorithms=[CONFIG.JWT_ALG],
            #     audience="authenticated",  # or whatever you saw above
            # )
            logger.debug("Decoded claims: %s", claims)
        except jwt.ExpiredSignatureError as e:
            logger.exception("Token expired")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.exception("Invalid Token error")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")
        except Exception as e:
            logger.exception("Exception decoding token")
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
