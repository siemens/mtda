# -*- coding: utf-8 -*-

from radish import before, after
from radish import world
from mtda.client import Client

import json
import os.path
import zerorpc

world.build = ''

@before.each_scenario
def init_mtda_client(scenario):
    scenario.context.client = Client()

@before.each_scenario
def load_settings(scenario):
    scenario.context.settings = {
        "boot": {
            "delay": 10
        }
    }
    if os.path.isfile("settings.json"):
        data = open("settings.json", "r").read()
        new_settings = scenario.context.settings.copy()
        loaded_settings = json.loads(data)
        new_settings.update(loaded_settings)
        scenario.context.settings = new_settings

@after.each_scenario
def destroy_mtda_client(scenario):
    del scenario.context.client
