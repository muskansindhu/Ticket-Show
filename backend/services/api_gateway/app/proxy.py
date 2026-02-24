import httpx
from fastapi import HTTPException, status


async def proxy_request(method: str, url: str, **kwargs):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text

            # Normalize proxied FastAPI error payloads like {"detail": "..."}
            # so clients receive a plain message instead of nested detail objects.
            if isinstance(detail, dict) and set(detail.keys()) == {"detail"}:
                detail = detail["detail"]

            raise HTTPException(
                status_code=e.response.status_code,
                detail=detail,
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unavailable",
            )
