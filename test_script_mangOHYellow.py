#!/usr/bin/python

import os
import os.path
import sys
import subprocess
import shlex
import tty
import termios
import serial
import time
import re

class TestResult(object):
    def __init__(self, success):
        self.success = success

class TestSuccess(TestResult):
    def __init__(self):
        super(TestSuccess, self).__init__(True)

class TestFailure(TestResult):
    def __init__(self, failure_msg):
        super(TestFailure, self).__init__(False)
        self.failure_msg = failure_msg

class Test(object):
    def __init__(self, name, run):
        self.name = name
        self.run = run

def test_buzzer():
    response = prompt_char("Press button and listen for buzzer. Did you hear buzzer? (Y)es, (N)o,")
    if response == 'Y':
        return TestSuccess()
    elif response == 'N':
        return TestFailure("User reported buzzer failure")

def test_headset():
    response = prompt_char("Plug in headset. Say something into headset, and listen for own voice echoed back through headset? (Y)es, (N)o,")
    if response == 'Y':
        return TestSuccess()
    elif response == 'N':
        return TestFailure("User reported headset failure")

def test_microphone():
    response = prompt_char("Say something into the on-board microphone, Listen for your own voice echoed back through headset? (Y)es, (N)o,")
    if response == 'Y':
        return TestSuccess()
    elif response == 'N':
        return TestFailure("User reported microphone failure")

def test_NFC():
    response = prompt_char("Bring NFC tag reader close to the mangOH board.Green LED flashes? (Y)es, (N)o,")
    if response == 'Y':
        return TestSuccess()
    elif response == 'N':
        return TestFailure("User reported NFC failure")

def test_light_sensor():
    response = prompt_char("Cover light sensor with finger and confirm software-controlled tri-colour LED goes blue? (Y)es, (N)o,")
    if response == 'Y':
        print "Cover light sensor test passed"
    elif response == 'N':
        return TestFailure("User reported light sensor failure")

    response = prompt_char("Uncover light sensor and confirm LED returns to yellow? (Y)es, (N)o,")
    if response == 'Y':
        print "Uncover light sensor test passed"
    elif response == 'N':
        return TestFailure("User reported light sensor failure")

    return TestSuccess()
            
def finalize_test():
    prompt_char("Switch cellular antenna selection DIP switch")

    response = prompt_char("Confirm software-controlled tri-colour LED has changed to white? (Y)es, (N)o,")
    if response == 'Y':
        print "Cover light sensor test passed"
    elif response == 'N':
        return TestFailure("User reported light sensor failure")

    response = prompt_char("Confirm hardware-controlled LED is yellow? (Y)es, (N)o,")
    if response == 'Y':
        print "Uncover light sensor test passed"
    elif response == 'N':
        return TestFailure("User reported light sensor failure")

    response = prompt_char("Press reset button. Hardware-controlled LED goes green? (Y)es, (N)o,")
    if response == 'Y':
        print "Uncover light sensor test passed"
    elif response == 'N':
        return TestFailure("User reported light sensor failure")

    prompt_char("Remove power jumper; Disconnect from USB; Disconnect battery;Unplug SIM, SD card, IoT card and expansion-connector test board.")

    return TestSuccess()

def write_eeprom():
    with open('/sys/bus/i2c/devices/0-0051/eeprom', 'w') as eeprom:
        eeprom.write("mangOH Red DV6.0 PCB Rev 6.0 with SWI MT7697 FW v4.3.0-0 - Manufactured by Talon Communications in Q4 2018\x00")

    return TestSuccess()

def prompt_char(p):
    print('  > ' + p)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return ch


def run_cmd(cmd, input=None):
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    (stdoutdata, stderrdata) = p.communicate(input)
    return (p.returncode, stdoutdata, stderrdata)


Tests = [
    Test("Buzzer", test_buzzer),
    Test("Headset", test_headset),
    Test("Microphone", test_microphone),
    Test("NFC", test_NFC),
    Test("Light", test_light_sensor),
    Test("finalize_test", finalize_test),
    Test("Write EEPROM", write_eeprom),
]


if __name__ == '__main__':
    print('+' + (78 * '-') + '+')
    print("|                        mangOH Red Test Program                               |")
    print('+' + (78 * '-') + '+')

    prompt_char("Plug in SIM, microSD card, IoT test card, and expansion-connector test board")
    prompt_char("Connect power jumper across pins 2 & 3")
    prompt_char("Confirm battery protect switch is ON (preventing the device from booting on battery power)")
    prompt_char("Connect battery")
    prompt_char("Switch battery protect switch OFF (allowing the device to boot on battery power)")
    prompt_char("Verify hardware-controlled tri-colour LED goes green")
    prompt_char("Connect unit to USB hub (both console and main USB")
    prompt_char("Wait for software-controlled tri-colour LED to turn green (ready for manual test)")
    prompt_char("Press button and listen for buzzer;")
    prompt_char("Plug in headset;")

    fail_count = 0
    for test in Tests:
        print "=== %s ===" % (test.name)
        r = test.run()
        if not r.success:
            fail_count += 1
            print("----->" + ' ' * 31 + "FAILURE" + ' ' * 30 + "<-----")
            for line in r.failure_msg.split('\n'):
                print("  | %s" % (line))
            print("-" * 80)
    print('-' * 80)
    if fail_count == 0:
        print "Completed: success"
    else:
        print "Completed: %d tests failed" % (fail_count)
    print("")

    sys.exit(fail_count)
