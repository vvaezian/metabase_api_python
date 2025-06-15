import httpx

async def get(self, endpoint, *args, **kwargs):
    """Async version of GET request"""
    await self.validate_session_async()
    auth = (self.email, self.password) if self.auth else None

    async with httpx.AsyncClient() as client:
        res = await client.get(
            self.domain + endpoint,
            headers=self.header,
            auth=auth,
            **kwargs
        )
        if 'raw' in args:
            return res
        else:
            return res.json() if res.status_code == 200 else False

async def post(self, endpoint, *args, **kwargs):
    """Async version of POST request"""
    await self.validate_session_async()
    auth = (self.email, self.password) if self.auth else None

    async with httpx.AsyncClient() as client:
        res = await client.post(
            self.domain + endpoint,
            headers=self.header,
            auth=auth,
            **kwargs
        )
        if 'raw' in args:
            return res
        else:
            return res.json() if res.status_code == 200 else False

async def put(self, endpoint, *args, **kwargs):
    """Async version of PUT request for updating objects"""
    await self.validate_session_async()
    auth = (self.email, self.password) if self.auth else None

    async with httpx.AsyncClient() as client:
        res = await client.put(
            self.domain + endpoint,
            headers=self.header,
            auth=auth,
            **kwargs
        )
        if 'raw' in args:
            return res
        else:
            return res.status_code

async def delete(self, endpoint, *args, **kwargs):
    """Async version of DELETE request"""
    await self.validate_session_async()
    auth = (self.email, self.password) if self.auth else None

    async with httpx.AsyncClient() as client:
        res = await client.delete(
            self.domain + endpoint,
            headers=self.header,
            auth=auth,
            **kwargs
        )
        if 'raw' in args:
            return res
        else:
            return res.status_code
