#!/bin/bash

cd ./FlashSequence
python 3 ./main.py
return_code=$?
wait
exit $return_code
