Feature: Linux kernel version compliance

    Background: Have Linux running
        Given my default build was flashed
        And my target is on
        And Linux is running

    Scenario: Test Linux kernel version
        When a kernel version is specified
        Then the running kernel version shall match
