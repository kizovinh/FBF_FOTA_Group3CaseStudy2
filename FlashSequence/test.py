from kizoDebug import *
from intelhex import IntelHex

def hex2bytes(hexNum):
    try:
        byte_data = bytes.fromhex(format(hexNum, 'X'))
        return byte_data
    except ValueError as e:
        print(f"Error: {e}")
        return None

def readHexFile(filePath):
    try:
        ih = IntelHex(filePath)

        extracted_data = bytes(ih.tobinarray())

        return extracted_data

    except FileNotFoundError:
        debug_print(f"Error: File not found.", level = DEBUG)
        return None
    except Exception as e:
        debug_print(f"Error: {e}", level = DEBUG)
        return None
    
def readHexFileByAddr(filePath, startAddr, endAddr):
    try:
        ih = IntelHex(filePath)

        start_index = int(format(startAddr, 'X'), 16)
        end_index   = int(format(endAddr, 'X'), 16)

        if end_index < start_index:
            print("Error: End address should be greater than or equal to start address.")
            return None

        extracted_data = bytes(ih.tobinarray(start=start_index, end=end_index))

        return extracted_data

    except FileNotFoundError:
        print("Error: File not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# ReqData = hex2bytes(0x80080000) + hex2bytes(0x8023FFFF)

fileContent = readHexFile("./FlashSequence/binInput/input.hex")

debug_print(fileContent, level=DEBUG)