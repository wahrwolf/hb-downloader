#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__license__ = "MIT"

import httpretty
from humble_downloader.humble_api.humble_api import HumbleApi
from humble_downloader.actions import Action
from test.fake_library.fake_library import FakeLibrary


@httpretty.activate
def test_httpbin():
    hapi = HumbleApi("AAAAAAA")
    fake = FakeLibrary(hapi)
    gamekeys = fake.gamekeys_list
    assert hapi.get_gamekeys() == gamekeys, "Game keys incorrectly retrieved"

    Action.list_downloads(hapi, gamekeys)  # TODO: capture and check STDOUT
    # TODO: also check Action.batch_download(hapi, game_keys)
