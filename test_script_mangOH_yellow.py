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

import threading


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


def read_light_sensor():
	light_sensor_path = "/sys/bus/iio/devices/iio:device1/in_illuminance_input"
	light_value = -1.0
	with open(light_sensor_path, 'r') as f:
		r = f.read()
		light_value = float(r)
		print "Light Sensor Value: %f" % light_value
	return light_value


def test_light_sensor():
	#     Cover light sensor with finger and confirm software-controlled tri-colour LED goes blue;
	#     (On-board test software should look for light sensor interrupt.)
	before_cover_value = read_light_sensor()
	resp = prompt_char("Please cover the light sensor with your finger").upper()
	after_cover_value = read_light_sensor()
	if before_cover_value - after_cover_value > 100:
		# triLED go blue
		triLED("red", "off")
		triLED("green", "off")
		triLED("blue", "on")
	
	while resp != "Y" and resp != "N":
		resp = prompt_char("Do you see blue light of LED? (Y/N)").upper()
	if resp == "N":
		return TestFailure("Light sensor has problem")

	#     Uncover light sensor and confirm LED returns to yellow;
	resp = prompt_char("Please uncover the light sensor").upper()
	after_uncover_value = read_light_sensor()
	if after_uncover_value - after_cover_value > 100:
		# triLED go yellow
		triLED("red", "on")
		triLED("green", "on")
		triLED("blue", "off")
	
	while resp != "Y" and resp != "N":
		resp = prompt_char("Do you see yellow light of LED? (Y/N)").upper()
	if resp == "N":
		return TestFailure("Light sensor has problem")

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
	p = subprocess.Popen(args, stdout=subprocess.PIPE,
						 stderr=subprocess.PIPE, stdin=subprocess.PIPE)
	(stdoutdata, stderrdata) = p.communicate(input)
	return (p.returncode, stdoutdata, stderrdata)

# return 0/-1
def generic_button_init():
	if os.path.exists("/sys/class/gpio/gpio25/"):
		print "Button already intialized"
	else:
		res = os.system("/bin/echo 25 > /sys/class/gpio/export")
		if res != 0:
			return -1
	return 0

# return 0/-1
def generic_button_deinit():
	res = os.system("/bin/echo 25 > /sys/class/gpio/unexport")
	if res != 0:
		return -1
	return 0

# return pressed/released/unknown
def generic_button_get_state():
	buttonFile = "/sys/class/gpio/gpio25/value"
	res = "unknown"
	with open(buttonFile, 'r') as f:
		r = f.read()
		if r[0] == "0":
			res = "pressed"
		elif r[0] == "1":
			res = "released"
		else:
			pass
	# print "Button is " + res
	return res

# freq: 0/1/1024/2048/4096/8192
def buzzer_set(freq=4096):
	bufferFile = "/sys/bus/i2c/drivers/rtc-pcf85063/4-0051/clkout_freq"
	with open(bufferFile, 'w') as f:
		f.write("%d"%freq)

def test_buzzer():
	#     Press button and listen for buzzer;

	resp = None
	bthread = ButtonMonitor()
	bthread.updateCallback(lambda : buzzer_set(), lambda : buzzer_set(0))
	bthread.start()

	resp = ""
	while resp != "Y" and resp != "N":
		resp = prompt_char("Press button and listen for buzzer\r\nDo you here the buzzer's sound when pressing button? (Y/N)").upper()
	if resp == "N":
		return TestFailure("Buzzer did not work")
	
	bthread.updateCallback()
	bthread.cancel.set()
	bthread.join()

	return TestSuccess()


class ButtonMonitor(threading.Thread):
	def __init__(self, activeCallback=None, inactiveCallback = None):
		threading.Thread.__init__(self)
		self.activeCallback = activeCallback
		self.inactiveCallback = inactiveCallback
		self.cancel = threading.Event()
		self.last_state = "unknown"

	def updateCallback(self, activeCallback=None, inactiveCallback = None):
		self.activeCallback = activeCallback
		self.inactiveCallback = inactiveCallback

	def run(self):
		while self.cancel.is_set() == False:
			button_state = generic_button_get_state()
			if button_state == "pressed":
				if self.last_state != button_state:
					self.last_state = button_state
					if self.activeCallback != None:
						# print "active callback"
						self.activeCallback()
			elif button_state == "released":
				if self.last_state != button_state:
					self.last_state = button_state
					if self.inactiveCallback != None:
						# print "in active callback"
						self.inactiveCallback()
			else:
				self.last_state = button_state
			time.sleep(0.1)

# led: red/green/blue
# state: on/off
def triLED(led="red", state="on"):
	triLEDRed = "/sys/devices/platform/expander.0/tri_led_red"
	triLEDGreen = "/sys/devices/platform/expander.0/tri_led_grn"
	triLEDBlue = "/sys/devices/platform/expander.0/tri_led_blu"

	ledFile = ""
	if led == "red":
		ledFile = triLEDRed
	elif led == "green":
		ledFile = triLEDGreen
	elif led == "blue":
		ledFile = triLEDBlue
	else:
		print "Unknown tri-LED"

	if state == "on":
		with open(ledFile, 'w') as f:
			f.write("1")
	elif state == "off":
		with open(ledFile, 'w') as f:
			f.write("0")
	else:
		print "Unknown LED state"

# state: on/off
def genericLED(state="on"):
	genericLEDPath = "/sys/devices/platform/expander.0/generic_led"

	if state == "on":
		with open(genericLEDPath, 'w') as f:
			f.write("1")
	elif state == "off":
		with open(genericLEDPath, 'w') as f:
			f.write("0")
	else:
		print "Unknown Generic LED state"

def yellowManualTest_initial():
	print "Plug in SIM, microSD card, IoT test card, and expansion-connector test board;"
	print "Connect power jumper across pins 2 & 3;"

	resp = ""
	while resp != "Y" and resp != "N":
		resp = prompt_char("Confirm \"battery protect\" switch is ON (preventing the device from booting on battery power)? (Y/N)").upper()
	if resp == "N":
		return TestFailure("Invalid setup for \"battery protect\" switch")
	
	print "Connect battery;"
	print "Switch \"battery protect\" switch OFF (allowing the device to boot on battery power);"
	
	resp = ""
	while resp != "Y" and resp != "N":
		resp = prompt_char("Could you see hardware-controller LED go green? (Y/N)").upper()
	if resp == "N":
		return TestFailure("The power has problem")
	print "Connect unit to USB hub (both console and main USB);"

	#     Wait for software-controlled tri-colour LED to turn green (ready for manual test);
	triLED("red", "off")
	triLED("green", "on")
	triLED("blue", "off")

	resp = ""
	while resp != "Y" and resp != "N":
		resp = prompt_char("Do you see software-controlled LED go green? (Y/N)").upper()
	if resp == "N":
		return TestFailure("Software-controller LED has problem")
	
	return TestSuccess()

def yellowManualTest_final():
	# 18. Switch cellular antenna selection DIP switch;
	prompt_char("Switch cellular antenna selection DIP switch")
	# 19. Press button to finalize the test;
	print "Press button to finalize the test"
	#     (On-board test software should verify that the correct string has been written to the NFC tag.)
	# 20. Confirm software-controlled tri-colour LED has changed to white;
	while True:
		if generic_button_get_state() == "pressed":
			triLED("red", "on")
			triLED("green", "on")
			triLED("blue", "on")
			break
		else:
			time.sleep(0.1)
	resp = ""
	while resp != "Y" and resp != "N":
		resp = prompt_char("Do you see software-controlled LED go white? (Y/N)").upper()
	if resp == "N":
		return TestFailure("Failed to final the test")
	
	# 21. Confirm hardware-controlled LED is yellow;
	resp = ""
	while resp != "Y" and resp != "N":
		resp = prompt_char("Do you see hardware-controlled LED go yellow? (Y/N)").upper()
	if resp == "N":
		return TestFailure("Wrong hardware-controlled LED state")
	
	# 22. Press reset button;
	# 23. Confirm hardware-controlled LED goes green;
	# 24. Remove power jumper;
	# 25. Disconnect from USB;
	# 26. Disconnect battery;
	# 27. Unplug SIM, SD card, IoT card and expansion-connector test board.
	return TestSuccess()

Tests = [
	
	Test("Initial", yellowManualTest_initial),
	Test("Buzzer", test_buzzer),
	Test("Light Sensor", test_light_sensor),
	Test("End", yellowManualTest_final),
]

if __name__ == '__main__':
	print('+' + (78 * '-') + '+')
	print("|                          mangOH Yellow Test Program                          |")
	print('+' + (78 * '-') + '+')

	# initial generic button
	if generic_button_init() != 0:
		print "Failed to initial Generic Button"
		sys.exit(-1)
	time.sleep(1)

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

	# deinitial generic button
	if generic_button_deinit() != 0:
		print "Failed to deinitial Generic Button"
		sys.exit(-1)
	time.sleep(1)
	
	sys.exit(fail_count)
