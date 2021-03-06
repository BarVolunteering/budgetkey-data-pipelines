import paramiko
import random
import time
import requests
import socket
import logging
import json
import os
import shutil
import tempfile
from selenium import webdriver


class google_chrome_driver():

    def __init__(self, wait=True):
        if wait:
            time.sleep(random.randint(1, 300))
        self.hostname = 'tzabar.obudget.org'
        self.hostname_ip = socket.gethostbyname(self.hostname)
        username = 'adam'
        self.port = random.randint(20000, 30000)
        # print('Creating connection for client #{}'.format(self.port))
        cmd = f'docker run -p {self.port}:{self.port} -p {self.port+1}:{self.port+1} -d akariv/google-chrome-in-a-box {self.port} {self.port+1}'

        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client._policy = paramiko.WarningPolicy()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.client.connect(username=username, hostname=self.hostname)
        stdin, stdout, stderr = self.client.exec_command(cmd)

        self.docker_container = None
        while not self.docker_container:
            time.sleep(3)
            self.docker_container = stdout.read().decode('ascii').strip()

        windows = None
        for i in range(10):
            time.sleep(6)
            try:
                windows = requests.get(f'http://{self.hostname_ip}:{self.port}/json/list').json()
                if len(windows) == 1:
                    break
            except Exception as e:
                logging.error('Waiting %s (%s): %s', i, windows, e)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.debugger_address = f'{self.hostname_ip}:{self.port}'
        self.driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=chrome_options)

    def teardown(self):
        # print('Closing connection for client #{}'.format(self.port))
        if self.docker_container:
            stdin, stdout, stderr = self.client.exec_command(f'docker stop {self.docker_container}')
            stdout.read()
        self.client.close()

    def json(self, url):
        self.driver.get(url)
        time.sleep(1)
        return json.loads(self.driver.find_element_by_css_selector('body > pre').text)

    def list_downloads(self):
        cmd = f'docker exec {self.docker_container} ls -1 /downloads/'
        _, stdout, _ = self.client.exec_command(cmd)
        return stdout.read().decode('utf8').split('\n')

    def download(self, url):
        expected = os.path.basename(url)
        for j in range(3):
            print('Attempt {}'.format(j))
            self.driver.get(url)
            downloads = []
            for i in range(10):
                time.sleep(6)
                downloads = self.list_downloads()
                if expected in downloads:
                    print('found {} in {}'.format(expected, downloads))
                    time.sleep(20)
                    out = tempfile.NamedTemporaryFile(delete=False, suffix=expected)
                    url = f'http://{self.hostname}:{self.port+1}/{expected}'
                    stream = requests.get(url, stream=True, timeout=30).raw
                    shutil.copyfileobj(stream, out)
                    out.close()
                    return out.name
        assert False, 'Failed to download file, %r' % downloads


def finalize(f):
    def func(package):
        yield package.pkg
        yield from package
        try:
            logging.warning('Finalizing connection')
            f()
        except Exception:
            logging.exception('Failed to finalize')
    return func


def finalize_teardown(gcd):
    return finalize(lambda: gcd.teardown())


if __name__ == '__main__':
    gcd = google_chrome_driver()
    c = gcd.driver
    c.get('http://data.gov.il/api/action/package_search')
    time.sleep(2)
    print(c.find_element_by_css_selector('body > pre').text)
    gcd.teardown()
