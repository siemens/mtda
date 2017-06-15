# -*- coding: utf-8 -*-

from radish import before, after
from mtda.main import MentorTestDeviceAgent

import json
import os.path
import zerorpc

@before.each_scenario
def init_agent(scenario):
    agent = MentorTestDeviceAgent()
    agent.load_config()
    if agent.remote is not None:
        uri = "tcp://%s:%d" % (agent.remote, agent.ctrlport)
        client = zerorpc.Client()
        client.connect(uri)
    else:
        client = agent
    scenario.context.agent  = agent
    scenario.context.client = client

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
def destory_agent(scenario):
    del scenario.context.agent
    del scenario.context.client

