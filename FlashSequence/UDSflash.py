from ComDia import *
from intelhex import IntelHex
import time
from udsoncan.client import Client
import udsoncan
import logging

def readBinFile(filePath) -> bytes:
    try:
        with open(filePath, 'rb') as file:
            buffer = file.read()

            file_size = len(buffer)
            
            logging.info(f"File Size: {file_size} bytes")

            return buffer

    except FileNotFoundError:
        logging.info(f"File not found: {filePath}")
    except Exception as e:
        logging.info(f"Error: {e}")

def readHexFile(filePath) -> bytes:
    try:
        ih = IntelHex(filePath)

        extracted_data = bytes(ih.tobinarray())

        return extracted_data

    except FileNotFoundError:
        logging.info(f"Error: File not found.")
        return None
    except Exception as e:
        logging.info(f"Error: {e}")
        return None
    
def readHexFileByAddr(filePath, startAddr, endAddr) -> bytes:
    try:
        ih = IntelHex(filePath)

        start_index = int(format(startAddr, 'X'), 16)
        end_index   = int(format(endAddr, 'X'), 16)

        if end_index < start_index:
            logging.info(f"Error: End address should be greater than or equal to start address.")
            return None

        extracted_data = bytes(ih.tobinarray(start=start_index, end=end_index))

        return extracted_data

    except FileNotFoundError:
        logging.info(f"Error: File not found.")
        return None
    except Exception as e:
        logging.info(f"Error: {e}")
        return None

def hex2bytes(hexNum) -> bytes:
    try:
        byte_data = bytes.fromhex(format(hexNum, 'X'))
        return byte_data
    except ValueError as e:
        logging.info(f"Error: {e}")
        return None

def unlockECU(client: Client):
    retVal_u8 = E_OK

    #Check Tester Connection
    logging.info("Changing Session to DEFAULT SESSION...")
    
    response = client.change_session(DEFAULT_SESSION)

    if response.positive:
        logging.info("!!!ECU is in DEFAULT SESSION!!!")
    else:
        return E_NOT_OK
    
    logging.info("Changing Session to SUPPLIER PROGRAMMING SESSION...")
    
    response = client.change_session(SUPPLIER_PROGRAMMING_SESSION)

    if response.positive:
        logging.info("!!!ECU is in SUPPLIER_PROGRAMMING_SESSION!!!")
    else:
        return E_NOT_OK
    
    time.sleep(1)
    logging.info("Changing Session to PROGRAMMING SESSION...")
    
    response = client.change_session(PROGRAMMING_SESSION)

    if response.positive:
        logging.info("!!!PROGRAMMING SESSION DONE!!!")
    else:
        return E_NOT_OK

    #Unlock Security
    logging.info("Hacking ECU...")
    
    response = client.unlock_security_access(DCM_SEC_LEVEL_1_2)

    if response.positive:
        logging.info("!!!ECU unlocked!!!")
    else:
        return E_NOT_OK

    return retVal_u8

# Dummy SID 27 SEED-KEY algorithm
def algoSeca(level: int ,seed : bytes ,params : dict) ->  bytes:
    keys = bytes([0 ,0 ,0 ,0])
    return keys

def caculateChecksum(fileContent) -> bytes:
    chkSum = sum (fileContent) & 0xFFFF
    return bytes([(chkSum & 0xFF00) >> 8, chkSum & 0xFF])
         
def flashSection(client: Client, section: CodeSection, flashMode, filePath):
    #Load file into buffer for flashing
    if flashMode == FLASH_USING_SINGLE_HEX_FILE:
        fileContent = readHexFileByAddr(filePath, section.start_address, section.end_address)
    elif flashMode == FLASH_USING_SPLITTED_HEX_FILE:
        fileContent = readHexFile(filePath)
    else:
        fileContent = readBinFile(filePath)
    
    ####################################   {section.name}    ######################################
    #Erase {section.name}
    logging.info(f"Erasing {section.name} from {section.start_address} to {section.end_address}...")
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
    
    response = client.start_routine( 0xFF00, ReqData)
    
    if response.positive:
        logging.info(f"!!!{section.name} erased!!!")
    else:
        logging.info(f"!!!{section.name} cannot be erased!!!")
        return E_NOT_OK

    #Request Download
    logging.info(f"Requesting for download {section.name}...")
    
    ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
    response = client.request_download(ReqData)

    if response.positive:
        logging.info(f"!!!Requested for download {section.name} successful!!!")
    else:
        logging.info(f"!!!Requested for download {section.name} unsuccessful!!!")
        return E_NOT_OK
    
    #Transfer Data
    logging.info(f"Start flashing {section.name}...")

    binFileSize     = len(fileContent)
    numBlockToFlash = int(int(binFileSize) / int(NUM_BYTES_FLASH))
    lastBlockSize   = binFileSize % NUM_BYTES_FLASH
    tempPtr         = 0

    logging.info(f"Bin file size:             {str(binFileSize)}")
    logging.info(f"Block size:                {str(NUM_BYTES_FLASH)}")
    logging.info(f"Number of Blocks to Flash: {str(numBlockToFlash)}")
    logging.info(f"LastBLK SIZE:              {str(lastBlockSize)}")

    for blkId in range(1, numBlockToFlash + 2):
        #logging.info("BlockID = {str(blkId & 0xFF)}")
        block_size = lastBlockSize if tempPtr >= (binFileSize - lastBlockSize) else NUM_BYTES_FLASH

        response = client.transfer_data(blkId & 0xFF, fileContent[tempPtr : tempPtr + block_size])

        if response.positive:
            tempPtr += block_size
        else:
            logging.info(f"Error while flashing {section.name} ({tempPtr} to {tempPtr + block_size})")        
            return E_NOT_OK
    
    #Request transfer exit
    client.request_transfer_exit()

    if response.positive:
        logging.info(f"!!!Transfer {section.name} exited!!!")        
    else:
        logging.info(f"Error while exiting transfer {section.name}")        
        return E_NOT_OK

    #validate the {section.name}
    logging.info(f"Validating {section.name} from {section.start_address} to {section.end_address}")
    
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address) + caculateChecksum(fileContent)
    
    response = client.start_routine(0xFF01, ReqData)
    
    if response.positive:
        logging.info(f"!!!{section.name} fineeee!!!")
    else:
        logging.info(f"!!!{section.name} validation ERROR!!!")
        return E_NOT_OK

def resetSoftware(client:Client):
    logging.info(f"Flashing completed, resetting the ECU...")

    client.ecu_reset(HARDRESET)

    logging.info(f"!!!All Done!!!")


def flash(client: Client, flashMode = FLASH_USING_SINGLE_HEX_FILE):
    retVal_u8 = E_NOT_OK

    # Unlock ECU
    retVal_u8 = unlockECU(client)

    if retVal_u8 == E_NOT_OK:
        logging.info("Not able to unlock ECU...")
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
        logging.info("FATAL ERROR WHILE FLASHING ASW0")
        return E_NOT_OK

    retVal_u8 = flashSection(client, oAsw1, flashMode, asw1FilePath)
    if retVal_u8 == E_NOT_OK:
        logging.info("FATAL ERROR WHILE FLASHING ASW0")
        return E_NOT_OK

    retVal_u8 = flashSection(client, oDs0, flashMode, ds0FilePath)
    if retVal_u8 == E_NOT_OK:
        logging.info("FATAL ERROR WHILE FLASHING ASW0")
        return E_NOT_OK

    return E_OK
    
    
