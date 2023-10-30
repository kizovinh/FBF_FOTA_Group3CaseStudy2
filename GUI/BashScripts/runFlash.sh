#!/bin/bash

cd ./FlashSequence
python ./main.py
return_code=$?
wait
exit $return_code
