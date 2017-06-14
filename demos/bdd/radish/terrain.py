# -*- coding: utf-8 -*-

from radish import before, after
from mtda.main import MultiTenantDeviceAccess

import zerorpc

@before.each_scenario
def init_agent(scenario):
    agent = MultiTenantDeviceAccess()
    agent.load_config()
    if agent.remote is not None:
        uri = "tcp://%s:%d" % (agent.remote, agent.ctrlport)
        client = zerorpc.Client()
        client.connect(uri)
    else:
        client = agent
    scenario.context.agent  = agent
    scenario.context.client = client

@after.each_scenario
def destory_agent(scenario):
    del scenario.context.agent
    del scenario.context.client

