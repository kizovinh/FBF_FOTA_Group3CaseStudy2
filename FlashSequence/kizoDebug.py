from datetime import datetime

DEBUG    = 1
INFO     = 2
WARNING  = 3
ERROR    = 4
CRITICAL = 5

SEPERATE_DIS = 15
DEBUG_LEVEL = DEBUG 

#function display message on console with OS time 
def display_message(message, level=DEBUG):
    if level >= DEBUG_LEVEL:
        now = datetime.now()
        print("{:<{distance}}{}".format(f"[{now:%H:%M:%S}]", f"{level}: {message}",distance = SEPERATE_DIS))

#function log message into log file
def log_message(message, level=1):
    if level >= DEBUG_LEVEL:
        with open(filename, 'a') as file:
            file.write(message + '\n')
    
#function display to console and log message into log file
def display_log_message(message, filename, level=1):
    display_message(message, level)
    log_message(message, level)
    
