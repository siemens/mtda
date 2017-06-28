Feature: Linux kernel version compliance

    Background: Have Linux running
        Given my default build was flashed
        And Linux was booted

    Scenario: Test Linux kernel version
        When a kernel version is specified
        Then the running kernel version shall match
