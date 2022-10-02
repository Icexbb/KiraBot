import json
from urllib import parse

import httpx
from nonebot import logger
from selenium import webdriver

from ..config import HTTPX_PROXY

TIMEOUT = httpx.Timeout(10, read=15)

CHROME_LOCATION = "C:/Program Files/Google/chrome/Application/chrome.exe"


def get_driver(use_proxy=False) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/96.0.4664.110 Safari/537.36'
    )
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-gpu')
    options.add_argument('--hide-scrollbars')
    if use_proxy:
        options.add_argument("--proxy-server=127.0.0.1:20001")
    if CHROME_LOCATION:
        options.binary_location = CHROME_LOCATION
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=options)
    return driver


async def async_get(url: str, proxy: bool = False, headers: dict = None, params: dict = None, **kwargs):
    try:
        async with httpx.AsyncClient(proxies=HTTPX_PROXY if proxy else None, timeout=TIMEOUT) as client:
            response = await client.get(url, headers=headers, params=params, **kwargs)
        assert response.status_code < 210, response.status_code
    except AssertionError as e:
        logger.error(f'Exception Happened when async get {url}:Status Code {e.args[0]}')
        with httpx.Client(proxies=HTTPX_PROXY if proxy else None, timeout=TIMEOUT) as client:
            response = client.get(url, params=params, headers=headers, **kwargs)
    return response


async def async_post(url: str, proxy: bool = False, headers: dict = None, data: dict = None, **kwargs):
    try:
        async with httpx.AsyncClient(proxies=HTTPX_PROXY if proxy else None, timeout=TIMEOUT) as client:
            response = await client.post(url, headers=headers, data=data, **kwargs)
        assert response.status_code < 210, response.status_code
    except AssertionError as e:
        logger.error(f'Exception Happened when async post {url}:Status Code {e.args[0]}')
        with httpx.Client(proxies=HTTPX_PROXY if proxy else None, timeout=TIMEOUT) as client:
            response = client.post(url, data=data, headers=headers, **kwargs)
    return response


async def async_head(url: str, proxy: bool = False, headers: dict = None, params: dict = None):
    try:
        async with httpx.AsyncClient(proxies=HTTPX_PROXY if proxy else None, timeout=TIMEOUT) as client:
            response = await client.head(url, headers=headers, params=params)
        assert response.status_code < 210, response.status_code
    except AssertionError as e:
        logger.error(f'Exception Happened when async head {url}:Status Code {e.args[0]}')
        with httpx.Client(proxies=HTTPX_PROXY if proxy else None, timeout=TIMEOUT) as client:
            response = client.head(url, params=params, headers=headers)
    return response


async def async_get_json(
        url: str, proxy: bool = False, headers: dict = None, params: dict = None
):
    response = await async_get(url, proxy, headers, params)
    try:
        result = response.json()
    except Exception as e:
        logger.error(f'Exception Happened when async get {url}')
        logger.exception(e)
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


def clean_url(url: str):
    clean = parse.urljoin(url, parse.urlparse(url).path)
    return clean
