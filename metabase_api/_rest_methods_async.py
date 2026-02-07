import httpx

async def get(self, endpoint, *args, **kwargs):
    await self.validate_session_async()
    auth = (self.email, self.password) if self.auth else None

    res = await self._client.get(endpoint, auth=auth, **kwargs)
    return res if "raw" in args else (res.json() if res.status_code == 200 else False)

async def post(self, endpoint, *args, **kwargs):
    await self.validate_session_async()
    auth = (self.email, self.password) if self.auth else None

    res = await self._client.post(endpoint, auth=auth, **kwargs)
    return res if "raw" in args else (res.json() if res.status_code == 200 else False)

async def put(self, endpoint, *args, **kwargs):
    await self.validate_session_async()
    auth = (self.email, self.password) if self.auth else None

    res = await self._client.put(endpoint, auth=auth, **kwargs)
    return res if "raw" in args else res.status_code

async def delete(self, endpoint, *args, **kwargs):
    await self.validate_session_async()
    auth = (self.email, self.password) if self.auth else None

    res = await self._client.delete(endpoint, auth=auth, **kwargs)
    return res if "raw" in args else res.status_code
