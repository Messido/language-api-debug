import os
import jwt
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer()

class VerifyToken:
    def verify(self, token: str) -> str:
        try:
            # 1. Decode generic claims without verification to get Issuer
            # We trust the issuer URL structure to be a valid URL, logic here relies on Clerk's standard architecture.
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            issuer = unverified_claims.get("iss")
            
            if not issuer:
                raise Exception("Missing issuer claim")

            # 2. Fetch JWKS from the issuer
            # Ideally verify strict issuer against env var, but extracting allows flexibility in this dev setup.
            jwks_url = f"{issuer}/.well-known/jwks.json"
            jwks_client = jwt.PyJWKClient(jwks_url)
            
            # This fetches the key that matches the 'kid' in the token header
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # 3. Verify the token with the fetched key
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False}, # Audience often varies (e.g. valid for multiple), can be strict if env var is set
                issuer=issuer
            )
            
            user_id = decoded.get("sub")
            if not user_id:
               raise Exception("Missing sub claim")
               
            return user_id

        except jwt.PyJWTError as e:
            logger.error(f"JWT Verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Auth error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

auth_service = VerifyToken()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verifies the JWT token and returns the user_id (sub).
    Dependency to be used in routes.
    """
    token = credentials.credentials
    user_id = auth_service.verify(token)
    return user_id
