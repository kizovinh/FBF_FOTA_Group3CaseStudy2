from kizoDebug import *
from ComDia import *

from can.interfaces.socketcan import SocketcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.configs import ClientConfig
from udsoncan.services import *
import udsoncan
import isotp
import time

from clsCodeSection import CodeSection

def readBinFile(filePath):
    try:
        with open(filePath, 'rb') as file:
            buffer = file.read()

        file_size = len(buffer)
        
        print(f"File Size: {file_size} bytes")

        return buffer

    except FileNotFoundError:
        debug_print(f"File not found: {filePath}", level = DEBUG)
    except Exception as e:
        debug_print(f"Error: {e}", level = DEBUG)

def hex2bytes(hexNum):
    try:
        byte_data = bytes.fromhex(format(hexNum, 'X'))
        return byte_data
    except ValueError as e:
        debug_print(f"Error: {e}", level = DEBUG)
        return None
    
def isSecaBypassed(seed: bytes):
    for i in range(0, len(seed)):
        if seed[i] == 0:
            ...
        else:
            return False
    return True

def unlockECU(client: Client):
    retVal_u8 = E_OK

    #Check Tester Connection
    debug_print("Changing Session to DEFAULT SESSION...", level = DEBUG)
    
    response = client.change_session(DEFAULT_SESSION)

    if response.positive:
        debug_print("!!!ECU is in DEFAULT SESSION!!!", level = DEBUG)
    else:
        return E_NOT_OK
    
    debug_print("Changing Session to PROGRAMMING SESSION...", level = DEBUG)
    
    response = client.change_session(SUPPLIER_PROGRAMMING_SESSION)

    if response.positive:
        debug_print("!!!ECU is in SUPPLIER_PROGRAMMING_SESSION!!!", level = DEBUG)
    else:
        return E_NOT_OK
    
    debug_print("Changing Session to PROGRAMMING SESSION...", level = DEBUG)
    time.sleep(1)
    response = client.change_session(PROGRAMMING_SESSION)
    
    if response.positive:
        debug_print("!!!PROGRAMMING SESSION DONE!!!", level = DEBUG)
    else:
        return E_NOT_OK

    #Unlock Security
    debug_print("Hacking ECU...", level = DEBUG)
    """
    response = client.request_seed(1)
    print (response)
    key = b'Helloooooooo'
    response = client.send_key(1, key)
    print (response)
    """
    
    response = client.unlock_security_access(DCM_SEC_LEVEL_1_2)
    print (response)
    """
    if response.positive:
        seed = response.data

        if isSecaBypassed(seed):
            debug_print("!!!ECU unlocked!!!", level = DEBUG)
        else:
            return E_NOT_OK
    else:
        return E_NOT_OK
   
    return retVal_u8
    """
def flashSection(client: Client, section: CodeSection, binFilePath):
    binFile = readBinFile(binFilePath)
    
    ####################################   {section.name}    ######################################
    #Erase {section.name}
    debug_print(f"Erasing {section.name} from {section.start_address} to {section.end_address}...", level = DEBUG)
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
    
    response = client.start_routine(0xFF00, ReqData)
    
    if response.positive:
        debug_print(f"!!!{section.name} erased!!!", level = DEBUG)
    else:
        debug_print(f"!!!{section.name} cannot be erased!!!", level = DEBUG)
        return E_NOT_OK
    
    #Request Download
    debug_print(f"Requesting for download {section.name}...", level = DEBUG)
    
    print(f"{section.size:08X}")
    ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
    
    response = client.request_download(ReqData)

    if response.positive:
        debug_print(f"!!!Requested for download {section.name} successful!!!", level = DEBUG)
    else:
        debug_print(f"!!!Requested for download {section.name} unsuccessful!!!", level = DEBUG)
        return E_NOT_OK
    
    #Transfer Data
    debug_print(f"Start flashing {section.name}...", level = DEBUG)

    binFileSize     = len(binFile)
    numBlockToFlash = int (binFileSize / NUM_BYTES_FLASH)
    lastBlockSize   = binFileSize % NUM_BYTES_FLASH
    tempPtr         = 0

    for blkId in range(1, numBlockToFlash + 1):
        block_size = lastBlockSize if tempPtr >= (binFileSize - lastBlockSize) else NUM_BYTES_FLASH
    
        response = client.transfer_data(blkId & 0xFF, binFile[tempPtr : tempPtr + block_size])

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

    #validate the {section.name}
    debug_print(f"Validating {section.name} from {section.start_address} to {section.end_address}", level = DEBUG)
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
    
    response = client.start_routine(0xFF01, ReqData)
    
    if response.positive:
        debug_print(f"!!!{section.name} fineeee!!!", level = DEBUG)
    else:
        #debug_print(f"!!!{section.nameON DONE!!! Hacking ECU...} validation ERROR!!!", level = DEBUG)
        debug_print("alkfjdlakjfdf")
        return E_NOT_OK

def resetSoftware(client:Client):
    debug_print(f"Flashing completed, resetting the ECU...", level = DEBUG)

    client.ecu_reset(HARDRESET)

    debug_print(f"!!!All Done!!!", level = DEBUG)


def flash(client: Client):
    retVal_u8 = E_NOT_OK

    # Unlock ECU
    retVal_u8 = unlockECU(client)

    if retVal_u8 == E_NOT_OK:
        debug_print("Not able to unlock ECU...", level=DEBUG)
        return E_NOT_OK

    #Start Flashing ASW0 + ASW1 + DS0
    retVal_u8 = flashSection(client, oAsw0, "./binInput/asw0.bin")
    if retVal_u8 == E_NOT_OK:
        debug_print("FATAL ERROR WHILE FLASHING ASW0", level=DEBUG)
        return E_NOT_OK

    retVal_u8 = flashSection(client, oAsw1, "./binInput/asw1.bin")
    if retVal_u8 == E_NOT_OK:
        debug_print("FATAL ERROR WHILE FLASHING ASW0", level=DEBUG)
        return E_NOT_OK

    retVal_u8 = flashSection(client, oDs0, "./binInput/ds0.bin")
    if retVal_u8 == E_NOT_OK:
        debug_print("FATAL ERROR WHILE FLASHING ASW0", level=DEBUG)
        return E_NOT_OK

    return E_OK
def Algo_Seca(level: int ,seed : bytes ,params : dict) ->  bytes:
    keys = bytes([0 ,0 ,0 ,0])
    return keys
    

if __name__ == "__main__":
    # Refer to isotp documentation for full details about parameters
    isotp_params = {
        'stmin'                       : 20,     # Will request the sender to wait 32ms between consecutive frame. 0-127ms or 100-900ns with values from 0xF1-0xF9
        'blocksize'                   : 0,      # Request the sender to send 8 consecutives frames before sending a new flow control message
        'wftmax'                      : 0,      # Number of wait frame allowed before triggering an error
        'tx_data_length'              : 8,      # Link layer (CAN layer) works with 8 byte payload (CAN 2.0)
        'tx_data_min_length'          : 8,      # 'tx_data_min_length': None,                                                          # Minimum length of CAN messages. When different from None, messages are padded to meet this length. Works with CAN 2.0 and CAN FD.
        'tx_padding'                  : 0x00,      # Will pad all transmitted CAN messages with byte 0x00.
        'rx_flowcontrol_timeout'      : 1000,   # Triggers a timeout if a flow control is awaited for more than 1000 milliseconds
        'rx_consecutive_frame_timeout': 1000,   # Triggers a timeout if a consecutive frame is awaited for more than 1000 milliseconds
        'squash_stmin_requirement'    : False,  # When sending,         respect the stmin requirement of the receiver. If set to True, go as fast as possible.
        'max_frame_size'              : 4095,    # Limit the size of receive frame.
    }

    # Link Layer (CAN protocol)
    bus     = SocketcanBus(channel='can0')
    #tp_addr = isotp.Address(isotp.AddressingMode.NormalFixed_29bits, source_address=0xFA, target_address=0x00)  # Network layer addressing scheme
    tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid = 0x6A2, rxid = 0x682)  # Network layer addressing scheme

    # Network/Transport layer (IsoTP protocol)
    stack = isotp.CanStack(bus=bus, address=tp_addr , params = isotp_params)
    stack.set_sleep_timing(0, 0)
    # Speed First (do not sleep)
    
    client_cfg1 = ClientConfig(
        use_server_timing = False,
        p2_star_timeout = 4.0,
        p2_timeout      = 4.0,
        security_algo = Algo_Seca,
        security_algo_params = {},
        server_memorysize_format = 32,
        server_address_format = 32
        )
    
    conn = PythonIsoTpConnection(stack)
    
    client = Client(conn, config = client_cfg1 ,request_timeout = None )
    
    with client:
        if flash(client) == E_OK:
            resetSoftware(client)
        else:
            debug_print(f"Flash unsuccessful, please see the logs above...", level = DEBUG)
    """
    with Client(conn, request_timeout = 5, config = client_cfg1) as client:
        if flash(client) == E_OK:
            resetSoftware(client)
        else:
            debug_print(f"Flash unsuccessful, please see the logs above...", level = DEBUG)
    """


