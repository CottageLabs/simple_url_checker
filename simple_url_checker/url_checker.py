import argparse
import csv
import dataclasses
import json
import logging
import time
from pathlib import Path
from typing import Iterable

from seleniumwire import webdriver
from seleniumwire.webdriver import DesiredCapabilities

from simple_url_checker import thread_utils

# path_driver = '/home/kk/app/chromedriver'
path_driver = None

log = logging.getLogger(__name__)


def get_driver(path_chrome_driver=None, user_agent=''):
    options = webdriver.ChromeOptions()

    # set user agent
    if user_agent == '':
        # user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/101.0.4951.44 Mobile/15E148 Safari/604.1"
        user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'

    if user_agent:
        options.add_argument(f'--user-agent={user_agent}')

    if path_chrome_driver:
        # run selenium with your local browser
        options.add_argument('--start-maximized')  # maximize browser window
        browser_driver = webdriver.Chrome(path_chrome_driver, options=options)
    else:
        # run selenium with docker remote browser
        options.add_argument("no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=800,600")
        options.add_argument("--disable-dev-shm-usage")
        browser_driver = webdriver.Remote(
            command_executor='http://127.0.0.1:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.CHROME,
            options=options,
            seleniumwire_options={
                'addr': '127.0.0.1',
            }
        )

    return browser_driver


@dataclasses.dataclass
class UrlResult:
    src_url: str
    src_status_code: int = None
    n_sub_req: int = None
    final_url: str = None
    final_status_code: int = None
    resp_content_len: int = None
    sub_requests: list['SubRequestResult'] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class SubRequestResult:
    url: str
    status_code: int | None
    resp_content_len: int
    headers: dict


def load_url_result(url: str) -> UrlResult:
    print(f'load_url_result({url})')
    driver = None
    url_result = UrlResult(src_url=url)
    try:
        driver = get_driver(path_driver)
        driver.get(url)
        sub_requests = []
        src_status_code = None
        final_status_code = None
        for r in driver.requests:
            resp_code = r.response.status_code if r.response else None
            sub_requests.append(SubRequestResult(url=r.url,
                                                 status_code=resp_code,
                                                 resp_content_len=len(r.response.body) if r.response else 0,
                                                 headers=r.response and dict(r.response.headers),
                                                 ))

            if r.url == url or r.url == url + '/':
                src_status_code = resp_code
            if driver.current_url == r.url:
                final_status_code = resp_code

        url_result = UrlResult(src_url=url,
                               src_status_code=src_status_code,
                               n_sub_req=len(driver.requests),
                               final_url=driver.current_url,
                               final_status_code=final_status_code,
                               resp_content_len=len(driver.page_source),
                               sub_requests=sub_requests,
                               )
    except Exception as e:
        log.error('something wrong when get url result with selenium')
        log.exception(e)
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    return url_result


def load_url_results(urls: Iterable[str], n_thread=40) -> Iterable[UrlResult]:
    return thread_utils.yield_run_fn_results(load_url_result, zip(urls), n_thread=n_thread)
    # for url in urls:
    #     yield load_url_result(url)


def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Simple URL checker")
    parser.add_argument('csv_path', type=str, help='Path to CSV file')
    parser.add_argument('-t', '--thread', type=int, default=10, help='Number of threads')
    # args = parser.parse_args(['/home/kk/Downloads/journal_info.csv'])
    args = parser.parse_args()

    urls = (row[1] for row in csv.reader(Path(args.csv_path).open('r')))
    next(urls)  # drop header
    # urls = itertools.islice(urls, 100)
    # urls = ['https://journals.sagepub.com/home/mac']
    # urls = [
    #     'https://www.google.com',
    #     'https://www.python.org',
    #     'https://www.yahoo.com',
    # ]

    n_url = 0
    with open('url_checker_results.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            f.name for f in dataclasses.fields(UrlResult) if f.name not in ['sub_requests']
        ])
        writer.writeheader()

        for url_result in load_url_results(urls, n_thread=args.thread):
            n_url += 1
            url_result.sub_requests = []
            result_dict = dataclasses.asdict(url_result)
            if 'sub_requests' in result_dict:
                del result_dict['sub_requests']

            print(json.dumps(result_dict, indent=4))
            writer.writerow(result_dict)

    print(f'done -- [{n_url}][{time.time() - start_time}]')


def main2():
    driver = get_driver('/home/kk/app/chromedriver')
    driver.get('https://journals.sagepub.com/home/mac')
    from time import sleep
    sleep(100)


if __name__ == '__main__':
    main()
