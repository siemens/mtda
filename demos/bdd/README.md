
# Overview

Demonstrate use of the Mentor Test Device Agent (or MTDA for short) from a Behavior
Driven Development (BDD) tool. Radish was used for this demonstration as steps may
be implemented in Python. The "mel" folder includes some sample feature tests such
as:

   * Support for USB mass storage devices

# Usage

Review the MTDA configuration in mtda.ini; you will most likely need to update the
hostname or IP address of the remote MTDA instance.

Tests may be started as follows:

```
$ radish mel/
```

# Sample output

Here is the output from a sample run:

```
Feature: Support for USB Mass Storage Devices  # mel/conformance/usb/msc.feature

    Background: Have Linux running
        Given my target is on
        And Linux is running

    Scenario: Test insertion of a mass storage device
      From Background: Have Linux running
        Given my target is on
        And Linux is running
      From Scenario
        Given my USB MSC device is detached
        And I have noted available disks
        When I attach my USB MSC device
        Then I expect new disk(s)

1 features (1 passed)
1 scenarios (1 passed)
4 steps (4 passed)
```

