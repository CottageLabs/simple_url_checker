""" try httpstatus.io Api to check url status """
import csv
import hashlib
import itertools

import json
from pathlib import Path
from time import sleep
from typing import Iterable

import requests

from simple_url_checker.url_checker import get_urls_from_journal_info_csv, UrlResult, create_url_result_csv

APP_HOME = Path.home() / 'tmp/httpstatusio/'
APP_HOME.mkdir(parents=True, exist_ok=True)

httpstatusio_key = '6qliPNvMWpM6CpoLZPOhGGGQ'
httpstatusio_url = 'https://api.httpstatus.io/v1/status'
if httpstatusio_key:
    httpstatusio_url = 'https://api.httpstatus.io/v1/pro/status'


def get_httpstatusio_response(url: str) -> dict:
    headers = {
        'Content-Type': 'application/json; charset=utf-8'
    }
    if httpstatusio_key:
        headers['x-api-key'] = httpstatusio_key

    data = {
        "requestUrl": url,
        "timings": True,
        "requestHeaders": True,
        "responseHeaders": True,
        "parsedUrl": True,
        "userAgent": "googlebot-smartphone",
        "rawRequest": True
    }
    response = requests.post(httpstatusio_url,
                             headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        # Success! Do something with the response...
        print(f'[Success] {url}')
    else:
        print(f'[Fail] {url} {response.status_code}')

    try:
        return response.json()
    except Exception as e:
        return {}


def get_urls(size=None):
    urls = get_urls_from_journal_info_csv('/home/kk/Downloads/journal_info.csv')
    if size:
        urls = itertools.islice(urls, size)
    return urls


def get_json_path(url):
    file_name = hashlib.sha1(url.encode('utf-8')).hexdigest()
    file_name = f'{file_name}.json'
    json_path = APP_HOME / file_name
    return json_path


def main(n_url=None):
    # urls = [
    #     "https://medicaljournalssweden.se/actadv"
    # ]
    urls = get_urls(size=n_url)

    for i, url in enumerate(urls):
        print(f'checking [{i}] [{url}]')
        json_path = get_json_path(url)
        if json_path.exists():
            print(f'already exists {json_path}')
            continue

        resp_json = get_httpstatusio_response(url)
        resp_json_str = json.dumps(resp_json, indent=4)
        json_path.write_text(resp_json_str)
        print(resp_json_str)
        print(f'write to {json_path}')
        sleep(0.51)  # avoid rate limit and 429


def load_httpstatusio_responses() -> Iterable[dict]:
    for i, url in enumerate(get_urls()):
        json_path = get_json_path(url)
        if not json_path.exists():
            print(f'not exists [{url}] [{json_path}]')
            continue

        resp_dict = json.loads(json_path.read_text())
        yield resp_dict


def to_csv_dict(resp: dict):
    resp_chain = resp['response'].get('chain')
    if not resp_chain:
        return UrlResult(src_url=resp['response']['url'],)

    return UrlResult(src_url=resp_chain[0]['url'],
                     src_status_code=resp_chain[0]['statusCode'],
                     n_sub_req=resp['response']['numberOfRedirects'],
                     final_url=resp_chain[-1]['url'],
                     final_status_code=resp_chain[-1]['statusCode'],
                     resp_content_len=resp_chain[-1]['responseHeaders'].get('content-length', None),
                     sub_requests=[],
                     )


def convert_json_to_csv():
    resp_dict_list = load_httpstatusio_responses()
    url_result_list = map(to_csv_dict, resp_dict_list)
    create_url_result_csv(url_result_list, 'hsio_url_checker_results.csv')


if __name__ == '__main__':
    # main(n_url=None)
    convert_json_to_csv()
