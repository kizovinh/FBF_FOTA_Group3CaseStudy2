from kizoDebug import *
from ComDia import *
from intelhex import IntelHex
import time
from udsoncan.client import Client
import udsoncan

def readBinFile(filePath):
    try:
        with open(filePath, 'rb') as file:
            buffer = file.read()

            file_size = len(buffer)
            
            debug_print(f"File Size: {file_size} bytes", level = DEBUG)

            return buffer

    except FileNotFoundError:
        debug_print(f"File not found: {filePath}", level = DEBUG)
    except Exception as e:
        debug_print(f"Error: {e}", level = DEBUG)

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
        debug_print(f"Error: File not found.", level = DEBUG)
        return None
    except Exception as e:
        debug_print(f"Error: {e}", level = DEBUG)
        return None

def hex2bytes(hexNum):
    try:
        byte_data = bytes.fromhex(format(hexNum, 'X'))
        return byte_data
    except ValueError as e:
        debug_print(f"Error: {e}", level = DEBUG)
        return None

def unlockECU(client: Client):
    retVal_u8 = E_OK

    #Check Tester Connection
    debug_print("Changing Session to DEFAULT SESSION...", level = DEBUG)
    
    response = client.change_session(DEFAULT_SESSION)

    if response.positive:
        debug_print("!!!ECU is in DEFAULT SESSION!!!", level = DEBUG)
    else:
        return E_NOT_OK
    
    debug_print("Changing Session to SUPPLIER PROGRAMMING SESSION...", level = DEBUG)
    
    response = client.change_session(SUPPLIER_PROGRAMMING_SESSION)

    if response.positive:
        debug_print("!!!ECU is in SUPPLIER_PROGRAMMING_SESSION!!!", level = DEBUG)
    else:
        return E_NOT_OK
    
    time.sleep(1)
    debug_print("Changing Session to PROGRAMMING SESSION...", level = DEBUG)
    
    response = client.change_session(PROGRAMMING_SESSION)

    if response.positive:
        debug_print("!!!PROGRAMMING SESSION DONE!!!", level = DEBUG)
    else:
        return E_NOT_OK

    #Unlock Security
    debug_print("Hacking ECU...", level = DEBUG)
    
    response = client.unlock_security_access(DCM_SEC_LEVEL_1_2)

    if response.positive:
        debug_print("!!!ECU unlocked!!!", level = DEBUG)
    else:
        return E_NOT_OK

    return retVal_u8

# Dummy SID 27 SEED-KEY algorithm
def Algo_Seca(level: int ,seed : bytes ,params : dict) ->  bytes:
    keys = bytes([0 ,0 ,0 ,0])
    return keys
def rtn_chksum (fileContent):
    chkSum = sum (fileContent) & 0xFFFF
    return bytes([(chkSum & 0xFF00) >> 8, chkSum & 0xFF])
    """
    asw0FilePath = "./binInput/asw0_notCompressed.bin"
    fileContent = readBinFile(asw0FilePath)
    binFileSize     = len(fileContent)
    print (hex(fileContent[binFileSize-8]))
    print (hex(fileContent[binFileSize-7]))
    print (hex(fileContent[binFileSize-6]))
    print (hex(fileContent[binFileSize-5]))
    """   
         
def flashSection(client: Client, section: CodeSection, flashMode, filePath):
    if flashMode == FLASH_USING_SINGLE_HEX_FILE:
        fileContent = readHexFileByAddr(filePath, section.start_address, section.end_address)
    elif flashMode == FLASH_USING_SPLITTED_HEX_FILE:
        fileContent = readHexFile(filePath)
    else:
        fileContent = readBinFile(filePath)
    
    ####################################   {section.name}    ######################################
    #Erase {section.name}
    debug_print(f"Erasing {section.name} from {section.start_address} to {section.end_address}...", level = DEBUG)
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
    
    response = client.start_routine( 0xFF00, ReqData)
    
    if response.positive:
        debug_print(f"!!!{section.name} erased!!!", level = DEBUG)
    else:
        debug_print(f"!!!{section.name} cannot be erased!!!", level = DEBUG)
        return E_NOT_OK

    #Request Download
    debug_print(f"Requesting for download {section.name}...", level = DEBUG)
    
    ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
    response = client.request_download(ReqData)

    if response.positive:
        debug_print(f"!!!Requested for download {section.name} successful!!!", level = DEBUG)
    else:
        debug_print(f"!!!Requested for download {section.name} unsuccessful!!!", level = DEBUG)
        return E_NOT_OK
    
    #Transfer Data
    debug_print(f"Start flashing {section.name}...", level = DEBUG)
    binFileSize     = len(fileContent)
    numBlockToFlash = int(int(binFileSize) / int(NUM_BYTES_FLASH))
    lastBlockSize   = binFileSize % NUM_BYTES_FLASH
    tempPtr         = 0
    print ("Bin file size " + str(binFileSize))
    print ("Num bytes flash " + str(NUM_BYTES_FLASH))
    print ("Number Block to Flash " + str(numBlockToFlash))
    print ("LastBLIK SIZE " + str(lastBlockSize))
    for blkId in range(1, numBlockToFlash + 2):
        #print ("BlockID = " + str(blkId & 0xFF))
        block_size = lastBlockSize if tempPtr >= (binFileSize - lastBlockSize) else NUM_BYTES_FLASH

        response = client.transfer_data(blkId & 0xFF, fileContent[tempPtr : tempPtr + block_size])

        if response.positive:
            tempPtr += block_size
        else:
            debug_print(f"Error while flashing {section.name} ({tempPtr} to {tempPtr + block_size})", level = DEBUG)        
            return E_NOT_OK
    
    #Request transfer exit
    client.request_transfer_exit()

    if response.positive:
        debug_print(f"!!!Transfer {section.name} exited!!!", level = DEBUG)        
    else:
        debug_print(f"Error while exiting transfer {section.name}", level = DEBUG)        
        return E_NOT_OK

    #binFileSize     = len(fileContent)
    #validate the {section.name}
    debug_print(f"Validating {section.name} from {section.start_address} to {section.end_address}", level = DEBUG)
    
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address) + rtn_chksum (fileContent)
    
    response = client.start_routine(0xFF01, ReqData)
    
    if response.positive:
        debug_print(f"!!!{section.name} fineeee!!!", level = DEBUG)
    else:
        debug_print(f"!!!{section.name} validation ERROR!!!", level = DEBUG)
        return E_NOT_OK

def resetSoftware(client:Client):
    debug_print(f"Flashing completed, resetting the ECU...", level = DEBUG)

    client.ecu_reset(HARDRESET)

    debug_print(f"!!!All Done!!!", level = DEBUG)


def flash(client: Client, flashMode = FLASH_USING_SINGLE_HEX_FILE):
    retVal_u8 = E_NOT_OK

    # Unlock ECU
    retVal_u8 = unlockECU(client)

    if retVal_u8 == E_NOT_OK:
        debug_print("Not able to unlock ECU...", level=DEBUG)
        return E_NOT_OK


    #Start Flashing ASW0 + ASW1 + DS0
    if flashMode == FLASH_USING_SPLITTED_HEX_FILE:
        asw0FilePath = "./binInput/asw0.hex"
        asw1FilePath = "./binInput/asw1.hex"
        ds0FilePath  = "./binInput/ds0.hex"
    elif flashMode == FLASH_USING_SINGLE_HEX_FILE:
        asw0FilePath = "./binInput/input.hex"
        asw1FilePath = "./binInput/input.hex"
        ds0FilePath  = "./binInput/input.hex"
    elif flashMode == FLASH_USING_BIN_FILE:
        asw0FilePath = "./binInput/asw0_notCompressed.bin"
        asw1FilePath = "./binInput/asw1_notCompressed.bin"
        ds0FilePath  = "./binInput/ds0_notCompressed.bin"
    elif flashMode == FLASH_USING_COMPRESSED_BIN_FILE:
        asw0FilePath = "./binInput/asw0.bin"
        asw1FilePath = "./binInput/asw1.bin"
        ds0FilePath  = "./binInput/ds0.bin"

    retVal_u8 = flashSection(client, oAsw0, flashMode, asw0FilePath)
    if retVal_u8 == E_NOT_OK:
        debug_print("FATAL ERROR WHILE FLASHING ASW0", level=DEBUG)
        return E_NOT_OK

    retVal_u8 = flashSection(client, oAsw1, flashMode, asw1FilePath)
    if retVal_u8 == E_NOT_OK:
        debug_print("FATAL ERROR WHILE FLASHING ASW0", level=DEBUG)
        return E_NOT_OK

    retVal_u8 = flashSection(client, oDs0, flashMode, ds0FilePath)
    if retVal_u8 == E_NOT_OK:
        debug_print("FATAL ERROR WHILE FLASHING ASW0", level=DEBUG)
        return E_NOT_OK

    return E_OK
    
    
