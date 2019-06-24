#!/bin/bash

set -x

#swiflash -m wp85 -r
#rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi
#
#sleep 60
#
#swiflash -m wp85 -i wp85_components/red_dv6_production_test.spk
#rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi
#
#sleep 90

scp $MANGOH_ROOT/linux_kernel_modules/mt7697wifi/scripts/interfaces root@192.168.2.2:/etc/network/interfaces
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi

scp $MANGOH_ROOT/linux_kernel_modules/mt7697wifi/scripts/mtwifi root@192.168.2.2:/etc/init.d/mtwifi
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi

scp 440Hz.wav root@192.168.2.2:~/440Hz.wav
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi

scp test_script_mangOH_red.py root@192.168.2.2:~/test_script_mangOH_red.py
rc=$?; if [[ $? -ne 0 ]]; then exit $rc; fi
