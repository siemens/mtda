Feature: Support for USB Mass Storage Devices

    Background: Have Linux running
        Given my target is on
        And Linux is running

    Scenario: Test insertion of a mass storage device
        Given my USB MSC device is detached
        And I have noted available disks
        When I attach my USB MSC device
        Then I expect new disk(s)
