from kizoDebug import *
from ComDia import *

from can.interfaces.socketcan import SocketcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.services import *
import udsoncan
import isotp

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

def hex2bytes(hexString):
    try:
        # Chuyển đổi chuỗi hex thành dữ liệu bytes
        byte_data = bytes.fromhex(hexString)
        return byte_data
    except ValueError as e:
        debug_print(f"Error: {e}", level = DEBUG)
        return None

def unlockECU(client: Client):
    retVal_u8 = E_OK

    #Check Tester Connection
    debug_print("Changing Session to PROGRAMMING SESSION...", level = DEBUG)
    
    response = client.change_session(PROGRAMMING_SESSION)

    if response.positive:
        debug_print("!!!PROGRAMMING SESSION DONE!!!", level = DEBUG)
    else:
        return E_NOT_OK

    #Unlock Security
    debug_print("Hacking ECU...", level = DEBUG)
    
    response = client.unlock_security_access(DCM_SEC_LEVEL_1_2, seed_params = None)

    if response.positive:
        bUnlocked = True
        data = response.data

        for i in range(0, len(data)):
            if data[i] == 0:
                ...
            else:
                bUnlocked = False

        if bUnlocked:
            debug_print("!!!ECU unlocked!!!", level = DEBUG)
        else:
            return E_NOT_OK
    else:
        return E_NOT_OK

    return retVal_u8

def flashSection(client: Client, section: CodeSection, binFile):
    ####################################   {section.name}    ######################################
    #Erase {section.name}
    debug_print(f"Erasing {section.name} from {section.start_address} to {section.end_address}", level = DEBUG)
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
    
    response = client.start_routine(0xFF00, ReqData)
    
    if response.positive:
        debug_print(f"!!!{section.name} erased!!!", level = DEBUG)
    else:
        return E_NOT_OK

    #Request Download
    debug_print(f"Requesting for download {section.name}...", level = DEBUG)
    
    ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
    response = client.request_download(ReqData)

    if response.positive:
        debug_print(f"!!!Requested for download {section.name} successful!!!", level = DEBUG)
    else:
        return E_NOT_OK
    
    #Transfer Data
    debug_print(f"Start flashing {section.name}...", level = DEBUG)

    binFileSize     = len(binFile)
    numBlockToFlash = binFileSize / NUM_BYTES_FLASH
    lastBlockSize   = binFileSize % NUM_BYTES_FLASH
    tempPtr         = 0

    for blkId in range(1, numBlockToFlash + 1):
        block_size = lastBlockSize if tempPtr >= (binFileSize - lastBlockSize) else NUM_BYTES_FLASH

        debug_print(f"Flashing {section.name} ({tempPtr} to {tempPtr + block_size})...", level = DEBUG)
        response = client.transfer_data(blkId, binFile[tempPtr : tempPtr + block_size])

        if response.positive:
            tempPtr += block_size
        else:
            return E_NOT_OK
    
    #Request transfer exit
    client.request_transfer_exit()
    if response.positive:
            ...
    else:
        return E_NOT_OK

    #validate the {section.name}
    debug_print(f"Validating {section.name} from {section.start_address} to {section.end_address}", level = DEBUG)
    
    ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
    
    response = client.start_routine(0xFF01, ReqData)
    
    if response.positive:
        debug_print(f"!!!{section.name} fineeee!!!", level = DEBUG)
    else:
        return E_NOT_OK

def resetSoftware(client:Client):
    debug_print(f"Flashing completed, resetting the ECU...", level = DEBUG)

    client.ecu_reset(HARDRESET)

    debug_print(f"!!!All Done!!!", level = DEBUG)


def flash(client: Client):
    if unlockECU(client) == E_NOT_OK:
        debug_print("Not able to unlock ECU...", level=DEBUG)

        return E_NOT_OK

    asw0BinFile = readBinFile("./asw0.bin") 
    flashSection(client, oAsw0, asw0BinFile)

    asw1BinFile = readBinFile("./asw1.bin") 
    flashSection(client, oAsw1, asw1BinFile)

    ds0BinFile = readBinFile("./ds0.bin") 
    flashSection(client, oDs0, ds0BinFile)

    resetSoftware(client)

if __name__ == "__main__":
    # Refer to isotp documentation for full details about parameters
    isotp_params = {
        'stmin': 32,    # Will request the sender to wait 32ms between consecutive frame. 0-127ms or 100-900ns with values from 0xF1-0xF9
        # Request the sender to send 8 consecutives frames before sending a new flow control message
        'blocksize': 8,
        'wftmax': 0,     # Number of wait frame allowed before triggering an error
        # Link layer (CAN layer) works with 8 byte payload (CAN 2.0)
        'tx_data_length': 8,
        # 'tx_data_min_length'           : None,  # Minimum length of CAN messages. When different from None, messages are padded to meet this length. Works with CAN 2.0 and CAN FD.
        'tx_data_min_length': 8,
        # Will pad all transmitted CAN messages with byte 0x00.
        'tx_padding': 0,
        # Triggers a timeout if a flow control is awaited for more than 1000 milliseconds
        'rx_flowcontrol_timeout': 1000,
        # Triggers a timeout if a consecutive frame is awaited for more than 1000 milliseconds
        'rx_consecutive_frame_timeout': 1000,
        # When sending,                                             respect the stmin requirement of the receiver. If set to True, go as fast as possible.
        'squash_stmin_requirement': False,
        'max_frame_size': 4095                # Limit the size of receive frame.
    }

    # Link Layer (CAN protocol)
    bus     = SocketcanBus(channel='can0')
    tp_addr = isotp.Address(isotp.AddressingMode.NormalFixed_29bits, source_address=0xFA, target_address=0x00)  # Network layer addressing scheme

    # Network/Transport layer (IsoTP protocol)
    stack = isotp.CanStack(bus=bus, address=tp_addr)
    stack.set_sleep_timing(0, 0)
    # Speed First (do not sleep)

    conn = PythonIsoTpConnection(stack)

    with Client(conn, request_timeout = 1) as client:
        flash(client)


