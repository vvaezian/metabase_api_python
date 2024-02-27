import requests


def get(self, endpoint, *args, **kwargs):
    self.validate_session()
    res = requests.get(
        self.domain + endpoint, headers=self.header, **kwargs, auth=self.auth
    )
    if "raw" in args:
        return res
    else:
        return res.json() if res.ok else False


def post(self, endpoint, *args, **kwargs):
    self.validate_session()
    res = requests.post(
        self.domain + endpoint, headers=self.header, **kwargs, auth=self.auth
    )
    if "raw" in args:
        return res
    else:
        return res.json() if res.ok else False


def put(self, endpoint, *args, **kwargs):
    """Used for updating objects (cards, dashboards, ...)"""
    self.validate_session()
    res = requests.put(
        self.domain + endpoint, headers=self.header, **kwargs, auth=self.auth
    )
    if "raw" in args:
        return res
    else:
        return res.status_code


def delete(self, endpoint, *args, **kwargs):
    self.validate_session()
    res = requests.delete(
        self.domain + endpoint, headers=self.header, **kwargs, auth=self.auth
    )
    if "raw" in args:
        return res
    else:
        return res.status_code
