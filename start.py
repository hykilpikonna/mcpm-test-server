#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import urllib.request
from datetime import datetime
import hypy_utils

import requests
import select

MAX_RAM = '4096M'
MIN_RAM = MAX_RAM
TIME = 5

version_re = re.compile('[0-9]\.[0-9]+\.[0-9]+')


def download_latest_purpur() -> str:
    latest = requests.get(f'https://api.purpurmc.org/v2/purpur/{ver}/latest').json()

    # Download update
    print(f'- Downloading...')
    new_f = f"purpur-{ver}-{latest['build']}.jar"
    urllib.request.urlretrieve(f"https://api.purpurmc.org/v2/purpur/{ver}/latest/download", new_f)

    # Check md5
    print(f'- Checking md5... ({latest["md5"]})')
    if hypy_utils.md5(new_f) == latest['md5']:
        print(f'- Checksum passed!')
    else:
        raise AssertionError('Checksum didn\'t pass.')

    return new_f


def update_server(f: str, ver: list[str]) -> str:
    # If no jar found, download latest purpur
    if f == '':
        print(f'No jar found, downloading latest purpur...')


    # Fetch latest purpur build
    if f.startswith('purpur'):
        ver = ver[0]
        build = int(re.findall('[0-9]{3,5}', f)[0])

        print(f'Checking release update for version {ver}... Current build: {build}')
        latest = requests.get(f'https://api.purpurmc.org/v2/purpur/{ver}/latest').json()
        latest_build = int(latest['build'])

        # Update
        if latest_build <= build:
            print('Already on latest version, nothing to do.')
            return f

        print(f'Updating from {build} to {latest_build}')

        new_f = download_latest_purpur()

        # Remove old file
        log_jar = f'logs/{datetime.today().strftime("%Y-%m-%d")}-{f}'
        shutil.move(f, log_jar)
        print(f'Old jar {f} moved to {log_jar}')

        return new_f


def update_plugins():
    # https://spiget.org/documentation/#!/resources/get_search_resources_query
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='start.py', description='Minecraft server starter')
    parser.add_argument('-j', '--java', help='Path to the Java executable.')
    parser.add_argument('--no-update', action='store_true', help='Disable auto update')
    args = parser.parse_args()

    java = args.java or 'java'

    # Find server jar
    jar = ''
    for f in os.listdir('.'):
        if not f.endswith('.jar'):
            continue

        ver = version_re.findall(f)
        if any(k in f for k in ['craftbukkit', 'spigot', 'paper', 'purpur']) or len(ver) != 0:
            jar = f
            break

    if not args.no_update:
        jar = update_server(jar, version_re.findall(jar))

    # Auto Restart
    while True:
        os.system(f'{java} -Xmx{MAX_RAM} -Xms{MIN_RAM} --add-modules=jdk.incubator.vector -jar {jar} nogui')

        print('Server stopped, restarting in 5s\nPress any key to stop the server.')
        i, o, e = select.select([sys.stdin], [], [], 5)
        if i:
            print('Server stops.')
            exit(0)
