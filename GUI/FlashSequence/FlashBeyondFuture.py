from kizoDebug import *
from ComDia import *
import time
from udsoncan.client import Client
import udsoncan

def readBinFile(filePath) -> bytes:
    with open(filePath, 'rb') as file:
        buffer = file.read()
        file_size = len(buffer)
        print_write_file(f"File Size: {file_size} bytes", level = DEBUG)
        return buffer

def readHexFile(filePath) -> bytes:
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
    
def readHexFileByAddr(filePath, startAddr, endAddr) -> bytes:
    try:
        ih = IntelHex(filePath)
        start_index = int(format(startAddr, 'X'), 16)
        end_index   = int(format(endAddr, 'X'), 16)
        if end_index < start_index:
            debug_print(f"Error: End address should be greater than or equal to start address.", level = DEBUG)
            return None
        extracted_data = bytes(ih.tobinarray(start=start_index, end=end_index))
        return extracted_data

    except FileNotFoundError:
        debug_print(f"Error: File not found.", level = DEBUG)
        return None
    except Exception as e:
        debug_print(f"Error: {e}", level = DEBUG)
        return None
        
def hex2bytes(hexNum) -> bytes:
    byte_data = bytes.fromhex(format(hexNum, 'X'))
    return byte_data

def unlockECU(client: Client):
    retVal_u8 = E_OK

    #Check Tester Connection
    print_write_file("Requesting change Session to DEFAULT SESSION...", level = INFO)
    try:
        response = client.change_session(DEFAULT_SESSION)
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file("Cannot request ECU to DEFAULT SESSION!!!", level = ERROR)
        return E_NOT_OK
    print_write_file("ECU is in DEFAULT SESSION!!!", level = INFO)
    
    print_write_file("Changing Session to SUPPLIER PROGRAMMING SESSION...", level = INFO)
    try:
        response = client.change_session(SUPPLIER_PROGRAMMING_SESSION)
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file("Cannot request ECU to SUPPLIER PROGRAMMING SESSION!!!", level = ERROR)
        return E_NOT_OK
    print_write_file("ECU is in SUPPLIER_PROGRAMMING_SESSION!!!", level = INFO)
    time.sleep(1)
    
    print_write_file("Changing Session to PROGRAMMING SESSION...", level = INFO)
    try:
        response = client.change_session(PROGRAMMING_SESSION)
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file("Cannot request ECU to PROGRAMMING SESSION!!!", level = ERROR)
        return E_NOT_OK
    print_write_file("PROGRAMMING SESSION DONE!!!", level = INFO)

    #Unlock Security
    print_write_file("Unlocking ECU...", level = INFO)
    try:
        response = client.unlock_security_access(DCM_SEC_LEVEL_1_2)
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file("Cannot request ECU to PROGRAMMING SESSION!!!", level = ERROR)
        return E_NOT_OK
    print_write_file("ECU unlocked!!!", level = INFO)

    return retVal_u8

# Dummy SID 27 SEED-KEY algorithm
def Algo_Seca(level: int ,seed : bytes ,params : dict) ->  bytes:
    keys = bytes([0 ,0 ,0 ,0])
    return keys

def rtn_chksum(fileContent):
    chkSum = sum (fileContent) & 0xFFFF
    return bytes([(chkSum & 0xFF00) >> 8, chkSum & 0xFF])
         
def flashSection(client: Client, section: CodeSection, flashMode, filePath):
    print_write_file(f"*******************************************************************************", level = INFO)
    print_write_file(f"*********************** Flash {section.name} ********************************************", level = INFO)
    print_write_file(f"*******************************************************************************", level = INFO)
    
    #Load file into buffer for flashing
    try:
        if flashMode == FLASH_USING_SINGLE_HEX_FILE:
            fileContent = readHexFileByAddr(filePath, section.start_address, section.end_address)
        elif flashMode == FLASH_USING_SPLITTED_HEX_FILE:
            fileContent = readHexFile(filePath)
        else:
            fileContent = readBinFile(filePath)
    except Exception as e:
        print_write_file(f"Cannot find {filePath}", level = ERROR)
        return E_NOT_OK
    
    ####################################   {section.name}    ######################################
    #Erase {section.name}
    print_write_file(f"Erasing {section.name} from {hex(section.start_address)} to {hex(section.end_address)}...", level = INFO)
    try:
        ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
    except Exception as e:
        print_write_file(f"{e}", level = ERROR)
        return E_NOT_OK
        
    # Resquest erase section
    try:
        response = client.start_routine( 0xFF00, ReqData)
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file(f"{section.name} cannot be erased!!!", level = ERROR)
        return E_NOT_OK
    print_write_file(f"{section.name} erased!!!", level = INFO)

    #Request Download
    print_write_file(f"Requesting for download {section.name}...", level = INFO)
    ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
    try:
        response = client.request_download(ReqData)
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file(f"Request for download {section.name} unsuccess!!!", level = ERROR)
        return E_NOT_OK
    print_write_file(f"Request for download {section.name} success!!!", level = INFO)
    
    #Transfer Data
    print_write_file(f"Start flashing {section.name}...", level = INFO)

    binFileSize     = len(fileContent)
    numBlockToFlash = int(int(binFileSize) / int(NUM_BYTES_FLASH))
    lastBlockSize   = binFileSize % NUM_BYTES_FLASH
    tempPtr         = 0

    print_debug(f"Bin file size:             {str(binFileSize)}", level = DEBUG)
    print_debug(f"Block size:                {str(NUM_BYTES_FLASH)}", level = DEBUG)
    print_debug(f"Number of Blocks to Flash: {str(numBlockToFlash)}", level = DEBUG)
    print_debug(f"LastBLK SIZE:              {str(lastBlockSize)}", level = DEBUG)

    for blkId in range(1, numBlockToFlash + 2):
        # finding approriate blocksize will be flashed
        block_size = lastBlockSize if tempPtr >= (binFileSize - lastBlockSize) else NUM_BYTES_FLASH
        try:
            response = client.transfer_data(blkId & 0xFF, fileContent[tempPtr : tempPtr + block_size])
            tempPtr += block_size
            # Calculate % flashed with gap 
            # flashing_percentage = 100 - float(tempPtr/binFileSize)*100 #flashing_percentage if ((100 - float(tempPtr/binFileSize) - flashing_percentage) < 2) else 100 - float(tempPtr/binFileSize)
            # print_debug(f"{section.name} flashed {flashing_percentage}", level = INFO)
            progressBar(f"{section.name} flashed ", tempPtr, binFileSize)
        except Exception as e:
            print_write_file(f"{e}", level = INFO)
            print_write_file(f"Error while flashing {section.name} ({tempPtr} to {tempPtr + block_size})", level = ERROR)
            return E_NOT_OK
    
    print_write_file("\n", level = INFO)
    print_write_file(f"{section.name} flashed successfully!", level = INFO)
    #Request transfer exit
    try:
        response = client.request_transfer_exit()
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file(f"Error while exiting transfer {section.name}", level = ERROR) 
        return E_NOT_OK
    print_write_file(f"Transfer {section.name} exited!!!", level = INFO)

    #validate the {section.name}
    print_write_file(f"Validating {section.name} from {hex(section.start_address)} to {hex(section.end_address)}", level = INFO)
    try:
        ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address) + rtn_chksum(fileContent)
    except Exception as e:
        print_write_file(f"{e}", level = ERROR)
        return E_NOT_OK
    
    # Request validate flashed data
    try:
        response = client.start_routine(0xFF01, ReqData)
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file(f"{section.name} validation ERROR!!!", level = ERROR)
        return E_NOT_OK
    print_write_file(f"{section.name} flashed validated!!!", level = INFO)
    
    return E_OK

def resetSoftware(client:Client):
    print_write_file(f"Flashing completed, resetting the ECU...", level = INFO)
    try:
        client.ecu_reset(HARDRESET)
    except Exception as e:
        print_write_file(f"{e}", level = INFO)
        print_write_file(f"Cannot reset ECU!!!", level = WARNING)
    print_write_file(f"New software flashed successfully!!!", level = DEBUG)
    
    return E_OK

def flash(client: Client, flashMode = FLASH_USING_SINGLE_HEX_FILE):
    
    retVal_u8 = E_NOT_OK
    # Unlock ECU
    retVal_u8 = unlockECU(client)

    if retVal_u8 == E_NOT_OK:
        print_write_file("Not able to unlock ECU...", level=INFO)
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
        asw0FilePath = "./binInput/Old/asw0_notCompressed.bin" 
        asw1FilePath = "./binInput/Old/asw1_notCompressed.bin" 
        ds0FilePath  = "./binInput/Old/ds0_notCompressed.bin" 
    elif flashMode == FLASH_USING_COMPRESSED_BIN_FILE:
        asw0FilePath = "./binInput/asw0.bin"
        asw1FilePath = "./binInput/asw1.bin"
        ds0FilePath  = "./binInput/ds0.bin"
        
    print_write_file(f"Required configuration completed", level = INFO)
    print_write_file(f"Start flashing sequence..", level = INFO)
    print_write_file(f"        ", level = INFO)
    
    retVal_u8 = flashSection(client, oAsw0, flashMode, asw0FilePath)
    if retVal_u8 == E_NOT_OK:
        print_write_file("FATAL ERROR WHILE FLASHING ASW0", level=ERROR)
        return E_NOT_OK

    retVal_u8 = flashSection(client, oAsw1, flashMode, asw1FilePath)
    if retVal_u8 == E_NOT_OK:
        print_write_file("FATAL ERROR WHILE FLASHING ASW1", level=ERROR)
        return E_NOT_OK

    retVal_u8 = flashSection(client, oDs0, flashMode, ds0FilePath)
    if retVal_u8 == E_NOT_OK:
        print_write_file("FATAL ERROR WHILE FLASHING DS0", level=ERROR)
        return E_NOT_OK

    return E_OK
    
    
