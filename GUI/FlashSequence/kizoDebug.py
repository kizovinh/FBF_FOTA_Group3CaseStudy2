import time
from datetime import datetime
import os
import sys

DEBUG    = 1
INFO     = 2
WARNING  = 3
ERROR    = 4
FINAl    = 5

#flag is used to indicate whether is at debugging phase
IS_DEBUGGING = False 

# This function is used to print message 
def print_debug(message, level):
    now = datetime.now()
    if level == ERROR:
        print(f"[{now:%H:%M:%S}]:  ERROR  : {message}")
    elif level == WARNING:
        print(f"[{now:%H:%M:%S}]:  WARNING: {message}")
    elif level == INFO:
        print(f"[{now:%H:%M:%S}]:  {message}")
    elif IS_DEBUGGING == True: 
        print(f"[{now:%H:%M:%S}]:  {message}")
    elif level == FINAl: 
        dummy = input(f"{message}")
        
# This function is used to write message to log file 
def debug_write_to_file(message, level):
    log_date = datetime.now().strftime("%Y%m%d_%H")
    now = datetime.now()
    dir_path = "/home/fbf/FBF_FOTA_Group3CaseStudy2/GUI/Logs"
    logfile_name = "%s/%s_log.log" % (dir_path, log_date)
    with open(logfile_name, 'a') as file:
        if level == ERROR:
            logging_content = f"[{now:%H:%M:%S}]:  ERROR  : {message}"
            file.write(logging_content + '\n')
        elif level == WARNING:
            logging_content = f"[{now:%H:%M:%S}]:  WARNING: {message}"
            file.write(logging_content + '\n')
        elif level == INFO:
            logging_content = f"[{now:%H:%M:%S}]:  {message}"
            file.write(logging_content + '\n')
        elif IS_DEBUGGING == True:
            logging_content = f"[{now:%H:%M:%S}]:  {message}"
            file.write(logging_content + '\n')

# This function is used to print and write message to log file 
def print_write_file(message, level):
    print_debug(message, level)
    debug_write_to_file(message, level)
    
# This function is used to print percentage to console 
def progressBar(message, count_value, total, suffix=''):
    bar_length = 60
    filled_up_Length = int(round(bar_length* count_value / float(total)))
    percentage = round(100.0 * count_value/float(total),1)
    bar = '=' * filled_up_Length + '-' * (bar_length - filled_up_Length)
    sys.stdout.write('%s [%s%s] %s%s ...%s\r' %(message, percentage, '%', bar,  suffix))
    sys.stdout.flush()
    
