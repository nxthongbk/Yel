#!/bin/bash
set -x

swiflash -m wp85 -r
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi

sleep 60

swiflash -m wp85 -i le19010_wp85_mangoh_yellow.spk
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi

sleep 90

scp test_script_mangOH_yellow.py root@192.168.2.2:~/test_script_mangOH_yellow.py
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi
