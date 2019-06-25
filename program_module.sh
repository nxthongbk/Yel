#!/bin/bash
scp test_script_mangOH_yellow.py root@192.168.2.2:~/test_script_mangOH_yellow.py
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi
