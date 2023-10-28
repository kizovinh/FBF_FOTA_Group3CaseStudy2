from kizoDebug import *
from ComDia import *
from intelhex import IntelHex
from clsCodeSection import CodeSection

from udsoncan.client import Client
import udsoncan

class Flash:
    def __init__(self, flash_sections: List[CodeSection]):
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
            'max_frame_size'              : 4095    # Limit the size of receive frame.
        }

        # Link Layer (CAN protocol)
        bus     = SocketcanBus(channel='can0')
        #tp_addr = isotp.Address(isotp.AddressingMode.NormalFixed_29bits, source_address=0xFA, target_address=0x00)  # Network layer addressing scheme
        tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid = 0x6A2, rxid = 0x682)  # Network layer addressing scheme

        # Network/Transport layer (IsoTP protocol)
        stack = isotp.CanStack(bus=bus, address=tp_addr , params = isotp_params)
        stack.set_sleep_timing(0, 0)
        # Speed First (do not sleep)

        client_cfg = ClientConfig(
            use_server_timing        = False,
            p2_star_timeout          = 4.0,
            p2_timeout               = 4.0,
            security_algo            = FlashBeyondFuture.Algo_Seca,
            security_algo_params     = {},
            server_memorysize_format = 32,
            server_address_format    = 32,
            request_timeout = None
            )
        conn = PythonIsoTpConnection(stack)
        
    def readBinFile(filePath):
        try:
            with open(filePath, 'rb') as file:
                buffer = file.read()
                file_size = len(buffer)
                display_message(f"File Size: {file_size} bytes", level = DEBUG)
                return buffer

        except FileNotFoundError:
            display_message(f"File not found: {filePath}", level = DEBUG)
            return E_NOT_OK
        except Exception as e:
            display_message(f"Error: {e}", level = DEBUG)
            return E_NOT_OK

    # def readHexFile(filePath):
        # try:
            # ih = IntelHex(filePath)
            # extracted_data = bytes(ih.tobinarray())
            # return extracted_data
        # except FileNotFoundError:
            # display_message(f"Error: File {filePath} not found.", level = DEBUG)
            # return E_NOT_OK
        # except Exception as e:
            # display_message(f"Error: {e}", level = DEBUG)
            # return E_NOT_OK
        
    # def readHexFileByAddr(filePath, startAddr, endAddr):
        # try:
            # ih = IntelHex(filePath)
            # start_index = int(format(startAddr, 'X'), 16)
            # end_index   = int(format(endAddr, 'X'), 16)
            # if end_index < start_index:
                # print("Error: End address should be greater than or equal to start address.")
                # return None
            # extracted_data = bytes(ih.tobinarray(start=start_index, end=end_index))
            # return extracted_data

        # except FileNotFoundError:
            # display_message(f"Error: {filePath} File not found.", level = DEBUG)
            # return E_NOT_OK
        # except Exception as e:
            # display_message(f"Error: {e}", level = DEBUG)
            # return E_NOT_OK

    def hex2bytes(hexNum):
        try:
            byte_data = bytes.fromhex(format(hexNum, 'X'))
            return byte_data
        except ValueError as e:
            display_message(f"Error: {e}", level = DEBUG)
            raise

    def unlockECU(client: Client):
        retVal_u8 = E_OK

        #Check Tester Connection
        display_message("Changing Session to DEFAULT SESSION...", level = DEBUG)
        try:
            response = client.change_session(DEFAULT_SESSION)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message("Cannot change session to DEFAULT SESSION...", level = DEBUG)
            return E_NOT_OK
            
        display_message("!!!ECU is in DEFAULT SESSION!!!", level = DEBUG)
        #Changing Session to SUPPLIER PROGRAMMING SESSION
        display_message("Requesting SUPPLIER PROGRAMMING SESSION SESSION...", level = DEBUG)
        try: 
            response = client.change_session(SUPPLIER_PROGRAMMING_SESSION)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message("Cannot change session to SUPPLIER PROGRAMMING SESSION...", level = DEBUG)
            return E_NOT_OK
        
        display_message("ECU is in SUPPLIER_PROGRAMMING_SESSION!!!", level = DEBUG)
        display_message("Requesting PROGRAMMING SESSION...", level = DEBUG)
        try:
            response = client.change_session(PROGRAMMING_SESSION)
            display_message("ECU is in PROGRAMMING SESSION DONE", level = DEBUG)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message("Cannot change session to PROGRAMMING SESSION...", level = DEBUG)
            return E_NOT_OK

        #Unlock Security
        display_message("Accessing ECU's security...", level = DEBUG)
        try:
            response = client.unlock_security_access(DCM_SEC_LEVEL_1_2)
            display_message("ECU's security accessed", level = DEBUG)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message("Cannot access ECU's security", level = DEBUG)
            return E_NOT_OK

        return retVal_u8

    # Dummy SID 27 SEED-KEY algorithm
    def Algo_Seca(level: int ,seed : bytes ,params : dict) ->  bytes:
        keys = bytes([0 ,0 ,0 ,0])
        return keys

    # Calculate checksum
    def checksum_calc(fileContent):
        chkSum = sum (fileContent) & 0xFFFF
        return bytes([(chkSum & 0xFF00) >> 8, chkSum & 0xFF])
             
    def flashSection(client: Client, section: CodeSection, filePath):
        # if flashMode == FLASH_USING_SINGLE_HEX_FILE:
            # fileContent = readHexFileByAddr(filePath, section.start_address, section.end_address)
        # elif flashMode == FLASH_USING_SPLITTED_HEX_FILE:
            # fileContent = readHexFile(filePath)
        # else:
            # fileContent = readBinFile(filePath)
        fileContent = readBinFile(filePath)
        ####################################   {section.name}    ######################################
        display_message(f"Flashing {section.name} section...", level = DEBUG)
        #Erase {section.name}
        display_message(f"{section.name} section from {section.start_address} to {section.end_address} will be erased ...", level = DEBUG)
        ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address)
        try:
            response = client.start_routine( 0xFF00, ReqData)
            display_message(f"Request erase {section.name} successfull...", level = DEBUG)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"Request erase {section.name} unsuccessfull !", level = DEBUG)
            return E_NOT_OK

        #Request Download
        display_message(f"Requesting for download {section.name}...", level = DEBUG)
        ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
        try:
            response = client.request_download(ReqData)
            display_message(f"Requested for download {section.name} successful", level = DEBUG)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"Requested for download {section.name} unsuccessful!!!", level = DEBUG)
            return E_NOT_OK
        
        #Transfer Data
        display_message(f"Start flashing {section.name}...", level = DEBUG)
        binFileSize     = len(fileContent)
        numBlockToFlash = int(int(binFileSize) / int(NUM_BYTES_FLASH))
        lastBlockSize   = binFileSize % NUM_BYTES_FLASH
        tempPtr         = 0
        display_message("Bin file size will be flashed:" + str(binFileSize))
        display_message("Num bytes flash " + str(NUM_BYTES_FLASH))
        display_message("Number Block to Flash " + str(numBlockToFlash))
        display_message("LastBLIK SIZE " + str(lastBlockSize))
        
        for blkId in range(1, numBlockToFlash + 2):
            block_size = lastBlockSize if tempPtr >= (binFileSize - lastBlockSize) else NUM_BYTES_FLASH
            try:
                response = client.transfer_data( (blkId&0xFF), fileContent[tempPtr : tempPtr + block_size])
                tempPtr += block_size
            except Exception as e:
                display_message(f"{e}", level = DEBUG)
                display_message(f"Error while flashing {section.name} ({tempPtr} to {tempPtr + block_size})", level = DEBUG)        
                return E_NOT_OK
        
        #Request transfer exit
        try:
            client.request_transfer_exit()
            display_message(f"!!!Transfer {section.name} exited!!!", level = DEBUG)    
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"Error while exiting transfer {section.name}", level = DEBUG)        
            return E_NOT_OK

        #validate the {section.name}
        display_message(f"Validating flashing {section.name} from {section.start_address} to {section.end_address}", level = DEBUG)
        ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address) + rtn_chksum(fileContent)
        try:
            response = client.start_routine(0xFF01, ReqData)
            display_message(f"Flashing {section.name} validated", level = DEBUG)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"{section.name} validation encounters errors", level = DEBUG)
            return E_NOT_OK

    def resetSoftware(client:Client):
        display_message(f"Flashing completed, resetting the ECU...", level = DEBUG)
        try: 
            client.ecu_reset(HARDRESET)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"Cannot reset ECU", level = DEBUG)


    def flash(client: Client, flash_sections: List[str]):
        retVal_u8 = E_NOT_OK
        
        # Unlock ECU
        retVal_u8 = unlockECU(client)

        if retVal_u8 == E_NOT_OK:
            display_message("Not able to unlock ECU...", level=DEBUG)
            return E_NOT_OK
            
        #Start Flashing ASW0 + ASW1 + DS0
        # if flashMode == FLASH_USING_SPLITTED_HEX_FILE:
            # asw0FilePath = "./binInput/asw0.hex"
            # asw1FilePath = "./binInput/asw1.hex"
            # ds0FilePath  = "./binInput/ds0.hex"
        # elif flashMode == FLASH_USING_SINGLE_HEX_FILE:
            # asw0FilePath = "./binInput/input.hex"
            # asw1FilePath = "./binInput/input.hex"
            # ds0FilePath  = "./binInput/input.hex"
        # elif flashMode == FLASH_USING_BIN_FILE:
            # asw0FilePath = "./binInput/asw0_notCompressed.bin"
            # asw1FilePath = "./binInput/asw1_notCompressed.bin"
            # ds0FilePath  = "./binInput/ds0_notCompressed.bin"
        # elif flashMode == FLASH_USING_COMPRESSED_BIN_FILE:
            # asw0FilePath = "./binInput/asw0.bin"
            # asw1FilePath = "./binInput/asw1.bin"
            # ds0FilePath  = "./binInput/ds0.bin"
        for section in flash_sections:
            if section == "asw0":
                filePath = "./binInput/asw0_notCompressed.bin"
                section: CodeSection = oAsw0
            elif section == "asw1":
                filePath = "./binInput/asw1_notCompressed.bin"
                section: CodeSection = oAsw1
            elif section == "ds0":
                filePath  = "./binInput/ds0_notCompressed.bin"
                section: CodeSection = oDs0
            else:
                display_message("This section type is not defined or supported", level=DEBUG)
            retVal_u8 = flashSection(client, section, filePath)
            if retVal_u8 == E_NOT_OK:
                display_message("FATAL ERROR WHILE FLASHING {section}", level=DEBUG)
                return E_NOT_OK

        return E_OK
    
    
