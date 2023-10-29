from kizoDebug import *
from ComDia import *
from intelhex import IntelHex
import time
from udsoncan.client import Client
import udsoncan

def readBinFile(filePath) -> bytes:
    try:
        with open(filePath, 'rb') as file:
            buffer = file.read()

            file_size = len(buffer)
            
            print_write_file(f"File Size: {file_size} bytes", level = DEBUG)

            return buffer

    except FileNotFoundError:
        print_write_file(f"File not found: {filePath}", level = DEBUG)
    except Exception as e:
        print_write_file(f"Error: {e}", level = DEBUG)

def readHexFile(filePath) -> bytes:
    try:
        ih = IntelHex(filePath)

        extracted_data = bytes(ih.tobinarray())

        return extracted_data

    except FileNotFoundError:
        print_write_file(f"Error: File not found.", level = DEBUG)
        return None
    except Exception as e:
        print_write_file(f"Error: {e}", level = DEBUG)
        return None
    
def readHexFileByAddr(filePath, startAddr, endAddr) -> bytes:
    response = client.tester_present()
    try:
        ih = IntelHex(filePath)

        start_index = int(format(startAddr, 'X'), 16)
        end_index   = int(format(endAddr, 'X'), 16)

        if end_index < start_index:
            print_write_file(f"Error: End address should be greater than or equal to start address.", level = DEBUG)
            return None

        response = client.tester_present()
        extracted_data = bytes(ih.tobinarray(start=start_index, end=end_index))

        return extracted_data

    except FileNotFoundError:
        print_write_file(f"Error: File not found.", level = DEBUG)
        return None
    except Exception as e:
        print_write_file(f"Error: {e}", level = DEBUG)
        return None

def hex2bytes(hexNum) -> bytes:
    try:
        byte_data = bytes.fromhex(format(hexNum, 'X'))
        return byte_data
    except ValueError as e:
        print_write_file(f"Error: {e}", level = DEBUG)
        return None

def unlockECU(client: Client):
    retVal_u8 = E_OK

    #Check Tester Connection
    print_write_file("Changing Session to DEFAULT SESSION...", level = DEBUG)
    
    response = client.change_session(DEFAULT_SESSION)

    if response.positive:
        print_write_file("!!!ECU is in DEFAULT SESSION!!!", level = DEBUG)
    else:
        return E_NOT_OK
    
    print_write_file("Changing Session to SUPPLIER PROGRAMMING SESSION...", level = DEBUG)
    
    response = client.change_session(SUPPLIER_PROGRAMMING_SESSION)

    if response.positive:
        print_write_file("!!!ECU is in SUPPLIER_PROGRAMMING_SESSION!!!", level = DEBUG)
    else:
        return E_NOT_OK
    
    time.sleep(1)
    print_write_file("Changing Session to PROGRAMMING SESSION...", level = DEBUG)
    
    response = client.change_session(PROGRAMMING_SESSION)

    if response.positive:
        print_write_file("!!!PROGRAMMING SESSION DONE!!!", level = DEBUG)
    else:
        return E_NOT_OK

    #Unlock Security
    print_write_file("Unlocking ECU...", level = DEBUG)
    
    response = client.unlock_security_access(DCM_SEC_LEVEL_1_2)

    if response.positive:
        print_write_file("!!!ECU unlocked!!!", level = DEBUG)
    else:
        return E_NOT_OK

    return retVal_u8

# Dummy SID 27 SEED-KEY algorithm
def Algo_Seca(level: int ,seed : bytes ,params : dict) ->  bytes:
    keys = bytes([0 ,0 ,0 ,0])
    return keys

def rtn_chksum(fileContent):
    chkSum = sum (fileContent) & 0xFFFF
    return bytes([(chkSum & 0xFF00) >> 8, chkSum & 0xFF])
         
def flashSection(client: Client, section: CodeSection, flashMode, filePath):
    print_write_file(f"*******************************************************************************", level = DEBUG)
    print_write_file(f"*********************** Flash {section.name} ********************************************", level = DEBUG)
    print_write_file(f"*******************************************************************************", level = DEBUG)
    
    #Load file into buffer for flashing
    if flashMode == FLASH_USING_SINGLE_HEX_FILE:
        fileContent = readHexFileByAddr(filePath, section.start_address, section.end_address)
    elif flashMode == FLASH_USING_SPLITTED_HEX_FILE:
        fileContent = readHexFile(filePath)
    else:
        fileContent = readBinFile(filePath)
    
    ####################################   {section.name}    ######################################
    #Erase {section.name}
    print_write_file(f"Erasing {section.name} from {section.start_address} to {section.end_address}...", level = DEBUG)
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
    
    response = client.start_routine( 0xFF00, ReqData)
    
    if response.positive:
        print_write_file(f"!!!{section.name} erased!!!", level = DEBUG)
    else:
        print_write_file(f"!!!{section.name} cannot be erased!!!", level = DEBUG)
        return E_NOT_OK

    #Request Download
    print_write_file(f"Requesting for download {section.name}...", level = DEBUG)
    
    ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
    response = client.request_download(ReqData)

    if response.positive:
        print_write_file(f"!!!Requested for download {section.name} successful!!!", level = DEBUG)
    else:
        print_write_file(f"!!!Requested for download {section.name} unsuccessful!!!", level = DEBUG)
        return E_NOT_OK
    
    #Transfer Data
    print_write_file(f"Start flashing {section.name}...", level = DEBUG)

    binFileSize     = len(fileContent)
    numBlockToFlash = int(int(binFileSize) / int(NUM_BYTES_FLASH))
    lastBlockSize   = binFileSize % NUM_BYTES_FLASH
    tempPtr         = 0

    print_write_file(f"Bin file size:             {str(binFileSize)}", level = DEBUG)
    print_write_file(f"Block size:                {str(NUM_BYTES_FLASH)}", level = DEBUG)
    print_write_file(f"Number of Blocks to Flash: {str(numBlockToFlash)}", level = DEBUG)
    print_write_file(f"LastBLK SIZE:              {str(lastBlockSize)}", level = DEBUG)

    for blkId in range(1, numBlockToFlash + 2):
        #print_write_file("BlockID = {str(blkId & 0xFF)}", level = DEBUG)
        block_size = lastBlockSize if tempPtr >= (binFileSize - lastBlockSize) else NUM_BYTES_FLASH

        response = client.transfer_data(blkId & 0xFF, fileContent[tempPtr : tempPtr + block_size])

        if response.positive:
            tempPtr += block_size
        else:
            print_write_file(f"Error while flashing {section.name} ({tempPtr} to {tempPtr + block_size})", level = DEBUG)        
            return E_NOT_OK
    
    #Request transfer exit
    response = client.request_transfer_exit()

    if response.positive:
        print_write_file(f"!!!Transfer {section.name} exited!!!", level = DEBUG)        
    else:
        print_write_file(f"Error while exiting transfer {section.name}", level = DEBUG)        
        return E_NOT_OK

    #validate the {section.name}
    print_write_file(f"Validating {section.name} from {section.start_address} to {section.end_address}", level = DEBUG)
    
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address) + rtn_chksum(fileContent)
    
    response = client.start_routine(0xFF01, ReqData)
    
    if response.positive:
        print_write_file(f"!!!{section.name} fineeee!!!", level = DEBUG)
    else:
        print_write_file(f"!!!{section.name} validation ERROR!!!", level = DEBUG)
        return E_NOT_OK

def resetSoftware(client:Client):
    print_write_file(f"Flashing completed, resetting the ECU...", level = DEBUG)

    client.ecu_reset(HARDRESET)

    print_write_file(f"!!!All Done!!!", level = DEBUG)


def flash(client: Client, flashMode = FLASH_USING_SINGLE_HEX_FILE):
    retVal_u8 = E_NOT_OK

    # Unlock ECU
    retVal_u8 = unlockECU(client)

    if retVal_u8 == E_NOT_OK:
        print_write_file("Not able to unlock ECU...", level=DEBUG)
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
        #/home/fbf/FBF_FOTA_Group3CaseStudy2/GUI/FlashSequence/binInput/Old/asw0_notCompressed.bin
        asw0FilePath = "./FlashSequence/binInput/Old/asw0_notCompressed.bin"
        asw1FilePath = "./FlashSequence/binInput/Old/asw1_notCompressed.bin"
        ds0FilePath  = "./FlashSequence/binInput/Old/ds0_notCompressed.bin"
    elif flashMode == FLASH_USING_COMPRESSED_BIN_FILE:
        asw0FilePath = "./binInput/asw0.bin"
        asw1FilePath = "./binInput/asw1.bin"
        ds0FilePath  = "./binInput/ds0.bin"

    # retVal_u8 = flashSection(client, oAsw0, flashMode, asw0FilePath)
    # if retVal_u8 == E_NOT_OK:
        # print_write_file("FATAL ERROR WHILE FLASHING ASW0", level=DEBUG)
        # return E_NOT_OK

    # retVal_u8 = flashSection(client, oAsw1, flashMode, asw1FilePath)
    # if retVal_u8 == E_NOT_OK:
        # print_write_file("FATAL ERROR WHILE FLASHING ASW1", level=DEBUG)
        # return E_NOT_OK

    # retVal_u8 = flashSection(client, oDs0, flashMode, ds0FilePath)
    # if retVal_u8 == E_NOT_OK:
        # print_write_file("FATAL ERROR WHILE FLASHING DS0", level=DEBUG)
        # return E_NOT_OK

    return E_OK
    
    
