Simple url checker prototype
----------------------------



How to run
----------

```shell
python3.11 -m venv ~/venv/simple-url-checker
. ~/venv/simple-url-checker/bin/activate
pip install -r requirements.txt
docker-compose -f docker/simle_url_checker/docker-compose.yml up -d
url_checker.py ~/Downloads/journal_info.csv
```

Cases to be study
-----------------

### normal case

```json
{
  "src_url": "https://sciendo.com/journal/BOKU",
  "src_status_code": 200,
  "n_sub_req": 98,
  "final_url": "https://sciendo.com/journal/BOKU",
  "final_status_code": 200,
  "resp_content_len": 200837
}
```

### redirect

```json
{
  "src_url": "http://www.uco.es/organiza/servicios/publica/az/az.htm",
  "src_status_code": 302,
  "n_sub_req": 77,
  "final_url": "https://www.uco.es/ucopress/az/index.php/az",
  "final_status_code": 200,
  "resp_content_len": 36991
}
```

### redirect to https

```json
{
  "src_url": "http://revistaseug.ugr.es/index.php/acfs",
  "src_status_code": 302,
  "n_sub_req": 25,
  "final_url": "https://revistaseug.ugr.es/index.php/acfs",
  "final_status_code": 200,
  "resp_content_len": 42571
}
```

### redirect to other domain

```json
{
  "src_url": "http://cca.hkd.hr/",
  "src_status_code": 301,
  "n_sub_req": 44,
  "final_url": "https://pubweb.carnet.hr/ccacaa/",
  "final_status_code": 200,
  "resp_content_len": 35186
}
```

### incorrect 403

```json
{
  "src_url": "https://www.idunn.no/edda",
  "src_status_code": 403,
  "n_sub_req": 7,
  "final_url": "https://www.idunn.no/edda",
  "final_status_code": 403,
  "resp_content_len": 10518
}
```


Other
-----

sometime seleniumwire could throw following exception if n_thread too large

```shell
OSError: [Errno 24] Too many open files: '/tmp/.seleniumwire/storage-0e072dbd-edf6-41c1-9922-579daa4ab194/request-c5ee580a-29f7-429c-9048
```

you can fix it by

```shell
ulimit -n 50000
```




TODO or to be improved
----------------

* fix url_checker throw selenium exception if n_thread > 40, it could be docker config issue
* selenium sometime return timeout
* selenium sometime can't create new session, only restart docker can fix it
```shell
Message: Could not start a new session. Error while creating session with the driver service. Stopping driver service: Could not start a new session. Response code 500. Message: unknown error: Chrome failed to start: exited abnormally.
```
* some request could be run by `requests` instead of selenium, it could be faster
* add db to cache result can improve performance

