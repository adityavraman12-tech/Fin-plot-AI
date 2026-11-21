import os
import httpx

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Authentication configuration missing"
        )

    try:
        response = httpx.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {token}"
            },
            timeout=10
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired authentication token"
            )

        user = response.json()

        return {
            "id": user["id"],
            "email": user.get("email")
        }

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Authentication service unavailable"
        )