import aiohttp

async def get(self, endpoint, *args, **kwargs):
    """Async version of GET request"""
    await self.validate_session_async()
    auth = aiohttp.BasicAuth(self.email, self.password) if self.auth else None
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            self.domain + endpoint, 
            headers=self.header, 
            auth=auth,
            **kwargs
        ) as res:
            if 'raw' in args:
                return res
            else:
                return await res.json() if res.status == 200 else False


async def post(self, endpoint, *args, **kwargs):
    """Async version of POST request"""
    await self.validate_session_async()
    auth = aiohttp.BasicAuth(self.email, self.password) if self.auth else None
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            self.domain + endpoint, 
            headers=self.header, 
            auth=auth,
            **kwargs
        ) as res:
            if 'raw' in args:
                return res
            else:
                return await res.json() if res.status == 200 else False


async def put(self, endpoint, *args, **kwargs):
    """Async version of PUT request for updating objects"""
    await self.validate_session_async()
    auth = aiohttp.BasicAuth(self.email, self.password) if self.auth else None
    
    async with aiohttp.ClientSession() as session:
        async with session.put(
            self.domain + endpoint, 
            headers=self.header, 
            auth=auth,
            **kwargs
        ) as res:
            if 'raw' in args:
                return res
            else:
                return res.status


async def delete(self, endpoint, *args, **kwargs):
    """Async version of DELETE request"""
    await self.validate_session_async()
    auth = aiohttp.BasicAuth(self.email, self.password) if self.auth else None
    
    async with aiohttp.ClientSession() as session:
        async with session.delete(
            self.domain + endpoint, 
            headers=self.header, 
            auth=auth,
            **kwargs
        ) as res:
            if 'raw' in args:
                return res
            else:
                return res.status
