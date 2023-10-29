#!/bin/bash

python3 ./FlashSequence/main.py
return_code=$?
wait
exit $return_code
