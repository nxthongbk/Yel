#!/bin/bash

scp test_script_mangOHYellow.py root@192.168.2.2:~/test_script_mangOHYellow.py
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi
