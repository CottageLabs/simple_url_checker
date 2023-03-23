import csv
import argparse
import dataclasses
import json
from pathlib import Path
from typing import Iterable

from seleniumwire import webdriver
from seleniumwire.webdriver import DesiredCapabilities

# path_driver = '/home/kk/app/chromedriver'
path_driver = None


def get_driver(path_chrome_driver=None):
    if path_chrome_driver:
        # run selenium with your local browser
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')  # maximize browser window
        browser_driver = webdriver.Chrome(path_chrome_driver, options=options)
    else:
        # run selenium with docker remote browser
        options = webdriver.ChromeOptions()
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

    # change user agent to avoid human detection from cloudflare
    browser_driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/101.0.4951.44 Mobile/15E148 Safari/604.1",
        "platform": "Windows"
    })
    return browser_driver


@dataclasses.dataclass
class UrlResult:
    src_url: str
    src_status_code: int | None
    n_sub_req: int
    final_url: str
    final_status_code: int | None
    resp_content_len: int
    sub_requests: list['SubRequestResult'] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class SubRequestResult:
    url: str
    status_code: int | None
    resp_content_len: int
    headers: dict


def load_url_results(urls: Iterable[str]) -> Iterable[UrlResult]:
    for url in urls:
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

        driver.quit()
        yield url_result


def main():
    parser = argparse.ArgumentParser(description="Simple URL checker")
    parser.add_argument('csv_path', type=str, help='Path to CSV file')
    # args = parser.parse_args(['/home/kk/Downloads/journal_info.csv'])
    args = parser.parse_args()

    urls = (row[1] for row in csv.reader(Path(args.csv_path).open('r')))
    next(urls)  # drop header
    # urls = ['https://journals.sagepub.com/home/mac']
    # urls = [
    #     'https://www.google.com',
    #     'https://www.python.org',
    #     'https://www.yahoo.com',
    # ]

    for url_result in load_url_results(urls):
        url_result.sub_requests = []
        result_dict = dataclasses.asdict(url_result)
        if 'sub_requests' in result_dict:
            del result_dict['sub_requests']
        print(json.dumps(result_dict, indent=4))


def main2():
    driver = get_driver('/home/kk/app/chromedriver')
    driver.get('https://journals.sagepub.com/home/mac')
    from time import sleep
    sleep(100)


if __name__ == '__main__':
    main2()
