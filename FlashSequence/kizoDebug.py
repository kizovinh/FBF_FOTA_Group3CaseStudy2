from datetime import datetime

DEBUG    = 1
INFO     = 2
WARNING  = 3
ERROR    = 4
CRITICAL = 5


DEBUG_LEVEL = DEBUG 

def debug_print(message, level=1):
    if level >= DEBUG_LEVEL:
        now = datetime.now()
        print(f"[{now:%H:%M:%S}]: {message}")

def debug_write_to_file(message, filename, level=1):
    if level >= DEBUG_LEVEL:
        with open(filename, 'a') as file:
            file.write(message + '\n')