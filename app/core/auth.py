import os
import jwt
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer()

class VerifyToken:
    # Cache clients to avoid repeated JWKS fetches (which triggers rate limits)
    _jwk_clients = {}

    def verify(self, token: str) -> str:
        try:
            # 1. Decode generic claims without verification to get Issuer
            # We trust the issuer URL structure to be a valid URL, logic here relies on Clerk's standard architecture.
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            issuer = unverified_claims.get("iss")
            
            if not issuer:
                raise Exception("Missing issuer claim")

            # 2. Fetch JWKS from the issuer (Cached with Retry)
            if issuer not in self._jwk_clients:
                jwks_url = f"{issuer}/.well-known/jwks.json"
                self._jwk_clients[issuer] = jwt.PyJWKClient(jwks_url)
            
            jwks_client = self._jwk_clients[issuer]
            
            try:
                # This fetches the key that matches the 'kid' in the token header
                signing_key = jwks_client.get_signing_key_from_jwt(token)
            except Exception as e:
                # If cached client fails (e.g. key rotation), clear cache and retry once
                logger.warning(f"Failed to get signing key from cache, retrying: {e}")
                del self._jwk_clients[issuer]
                jwks_url = f"{issuer}/.well-known/jwks.json"
                self._jwk_clients[issuer] = jwt.PyJWKClient(jwks_url)
                jwks_client = self._jwk_clients[issuer]
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
            logger.error(f"Auth error type: {type(e).__name__}, details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {type(e).__name__}",
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
