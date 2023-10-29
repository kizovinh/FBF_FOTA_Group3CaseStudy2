from datetime import datetime
import os

DEBUG    = 1
INFO     = 2
WARNING  = 3
ERROR    = 4
CRITICAL = 5


DEBUG_LEVEL = DEBUG 

def print_debug(message, level=1):
    if level >= DEBUG_LEVEL:
        now = datetime.now()
        print(f"[{now:%H:%M:%S}]: {message}")

def debug_write_to_file(message, level=1):
    if level >= DEBUG_LEVEL:
        now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        dir_path = "/home/fbf/FBF_FOTA_Group3CaseStudy2/GUI"
        logfile_name = "%s/%s.txt" % (dir_path, now)
        with open(logfile_name, 'a') as file:
            file.write(message + '\n')
            
def print_write_file(message, level=1):
    print_debug(message, level=1)
    debug_write_to_file(message, level=1)
