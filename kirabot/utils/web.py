import json

import httpx
from nonebot import logger

from ..config import HTTPX_PROXY

TIMEOUT = httpx.Timeout(15)


async def async_get(url: str, proxy: bool = False, headers: dict = None, params: dict = None):
    try:
        async with httpx.AsyncClient(proxies=HTTPX_PROXY if proxy else None, timeout=TIMEOUT) as client:
            response = await client.get(url, headers=headers, params=params)
        assert response.status_code == 200
    except Exception as e:
        logger.error(f'Exception "{e}" Happened when async get {url}')
        # logger.exception(e)
        with httpx.Client(proxies=HTTPX_PROXY if proxy else None, timeout=TIMEOUT) as client:
            response = client.get(url, params=params, headers=headers)
    return response


async def async_get_json(
        url: str, proxy: bool = False, headers: dict = None, params: dict = None
):
    response = await async_get(url, proxy, headers, params)
    try:
        result = response.json()
    except Exception as e:
        logger.error(f'Exception {e} Happened')
        result = json.loads(response.text, strict=False)
    return result


async def async_download(url: str, path: str, filename: str, proxy: bool = False, headers: dict = None):
    """异步下载文件"""
    # content = await async_get_content(url, proxy, headers)
    response = await async_get(url, proxy, headers)
    content = response.read()
    with open(path + filename, 'wb') as file_output:
        file_output.write(content)
        return True


async def async_get_content(url: str, proxy: bool = False, headers: dict = None, params: dict = None):
    response = await async_get(url, proxy, headers, params)
    return response.read()


yourls_token = "f9a7df5592"
yourls_api = "http://s.xbb.moe/yourls-api.php"


async def get_short_url(url: str):
    try:
        async with httpx.AsyncClient(proxies=HTTPX_PROXY, timeout=TIMEOUT) as client:
            querystring = {"action": "shorturl", "url": url, "signature": "f9a7df5592", "format": "json"}
            response = await client.get(yourls_api, params=querystring)
            assert response.status_code in [200, 400], "失败"
            shorturl = response.json()['shorturl']
            return shorturl
    except Exception as e:
        logger.error(f'Exception "{e}" Happened when get short url of {url}')
        return url
