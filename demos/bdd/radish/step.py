# -*- coding: utf-8 -*-

from radish import step, given, when, then

import time

@given("my target is on")
def target_is_on(step):
    client = step.context.client
    runtime = "???"
    status = client.target_status()
    if status == "OFF":
        client.target_on()
        # Give target plenty of time to start...
        time.sleep(90)
        status = client.target_status()

@step("Linux is running")
def linux_is_running(step):
    client = step.context.client
    step.context.runtime = "???"

    # Check for target console
    online = console_login(client)
    assert online == True

    # Check running system
    client.console_send("cat /proc/version\n")
    time.sleep(1)
    line = client.console_head() # Prompt + command
    line = client.console_head() # Command output (1st line)
    if line is not None and line.startswith("Linux "):
        step.context.runtime = "Linux"

    assert step.context.runtime == "Linux"

@given("my USB {className:w} device is detached")
def usb_device_detached(step, className):
    client = step.context.client
    step.context.usb_device_class = className

    # Detach the specified device
    offline = client.usb_off_by_class(className)
    assert offline == True

    # Give the runtime plenty of time to detect removal of the USB device
    time.sleep(1)

@when("I attach my USB {className:w} device")
def attach_usb_device(step, className):
    client = step.context.client
    step.context.usb_device_class = className

    # Detach the specified device
    online = client.usb_on_by_class(className)
    assert online == True

    # Give the runtime plenty of time to detect the USB device
    time.sleep(5)

@given("I have noted available disks")
def note_available_disks(step):
    client = step.context.client

    # Check for target console
    online = console_login(client)
    assert online == True

    # Get available disks
    results = client.console_run("cat diskstats|awk '{ print $3; }'")
    step.context.disks = results.split('\n')[1:-1]

@then("I expect new disk(s)")
def expect_new_disks(step):
    client = step.context.client

    # Check for target console
    online = console_login(client)
    assert online == True

    # Get available disks
    results = client.console_run("cat diskstats|awk '{ print $3; }'")
    disks = results.split('\n')[1:-1]

    assert step.context.disks is not None
    assert len(disks) > len(step.context.disks)

def console_check(client):

    line  = None
    tries = 3

    while line is None and tries > 0:
        client.console_clear()
        client.console_send("\3\n")
        time.sleep(1)
        line = client.console_tail()
        tries = tries - 1

    return line is not None

def console_prompt(client):

    online = False
    tries  = 3

    client.console_prompt("# ")

    while online == False and tries > 0:
        client.console_clear()
        client.console_send("\3\n")
        time.sleep(1)
        line = client.console_tail()
        if line is not None and line.endswith("# "):
            online = True
        tries = tries - 1

    return online

def console_login(client):

    # Check for target console
    online = console_check(client)
    assert online == True

    # Check if we need to login
    client.console_send("\3\n")
    time.sleep(1)
    line = client.console_tail()
    if line is not None and line.endswith("login: "):
        client.console_send("root\n")
        time.sleep(1)

    online = console_prompt(client)
    return online

