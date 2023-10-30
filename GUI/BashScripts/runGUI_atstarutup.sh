#!/bin/bash

while ! ping -c 1 google.com &>/dev/null; do
	sleep 5
done

cd ~/FBF_FOTA_Group3CaseStudy2/GUI/
lxterminal -e python3 rasp.py