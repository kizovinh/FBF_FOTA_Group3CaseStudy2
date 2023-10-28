from kizoDebug import *
from ComDia import *
from clsCodeSection import CodeSection

from can.interfaces.socketcan import SocketcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.configs import ClientConfig
from udsoncan.services import *
import isotp
import udsoncan

class Flash:
    def __init__(self, flash_sections: List[CodeSection]):
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
        self.stack = isotp.CanStack(bus=bus, address=tp_addr , params = isotp_params)
        # Speed First (do not sleep)
        self.stack.set_sleep_timing(0, 0)

        client_cfg = ClientConfig(
            use_server_timing        = False,
            p2_star_timeout          = 4.0,
            p2_timeout               = 4.0,
            security_algo            = self.Algo_Seca,
            security_algo_params     = {},
            server_memorysize_format = 32,
            server_address_format    = 32,
            request_timeout = None
            )
        self.conn = PythonIsoTpConnection(self.stack)
        self.client = Client(self.conn, config = client_cfg)
        self.flash_sections = flash_sections
        
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

    def hex2bytes(hexNum):
        byte_data = bytes.fromhex(format(hexNum, 'X'))
        return byte_data

    def unlockECU(self):
        retVal_u8 = E_OK

        #Check Tester Connection
        display_message("Changing Session to DEFAULT SESSION...", level = DEBUG)
        try:
            response = self.client.change_session(DEFAULT_SESSION)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message("Cannot change session to DEFAULT SESSION...", level = DEBUG)
            return E_NOT_OK
            
        display_message("!!!ECU is in DEFAULT SESSION!!!", level = DEBUG)
        #Changing Session to SUPPLIER PROGRAMMING SESSION
        display_message("Requesting SUPPLIER PROGRAMMING SESSION SESSION...", level = DEBUG)
        try: 
            response = self.client.change_session(SUPPLIER_PROGRAMMING_SESSION)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message("Cannot change session to SUPPLIER PROGRAMMING SESSION...", level = DEBUG)
            return E_NOT_OK
        display_message("ECU is in SUPPLIER_PROGRAMMING_SESSION!!!", level = DEBUG)
        
        #Changing Session to PROGRAMMING SESSION
        display_message("Requesting PROGRAMMING SESSION...", level = DEBUG)
        try:
            response = self.client.change_session(PROGRAMMING_SESSION)
            display_message("ECU is in PROGRAMMING SESSION DONE", level = DEBUG)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message("Cannot change session to PROGRAMMING SESSION...", level = DEBUG)
            return E_NOT_OK

        #Unlock Security
        display_message("Accessing ECU's security...", level = DEBUG)
        try:
            response = self.client.unlock_security_access(DCM_SEC_LEVEL_1_2)
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
    def checksum_calc(fileContent) -> bytes:
        chkSum = sum (fileContent) & 0xFFFF
        return bytes([(chkSum & 0xFF00) >> 8, chkSum & 0xFF])
             
    def flashSection(self, section: CodeSection):
        fileContent = self.readBinFile(section.path)
        ####################################   {section.name}    ######################################
        display_message(f"Flashing {section.name} section...", level = DEBUG)
        #Erase {section.name}
        display_message(f"{section.name} section from {section.start_address} to {section.end_address} will be erased ...", level = DEBUG)
        ReqData = self.hex2bytes(section.start_address) + hex2bytes(section.end_address)
        try:
            response = self.client.start_routine( 0xFF00, ReqData)
            display_message(f"Request erase {section.name} successfull...", level = DEBUG)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"Request erase {section.name} unsuccessfull !", level = DEBUG)
            return E_NOT_OK

        #Request Download
        display_message(f"Requesting for download {section.name}...", level = DEBUG)
        ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
        try:
            response = self.client.request_download(ReqData)
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
                response = self.client.transfer_data( (blkId&0xFF), fileContent[tempPtr : tempPtr + block_size])
                tempPtr += block_size
            except Exception as e:
                display_message(f"{e}", level = DEBUG)
                display_message(f"Error while flashing {section.name} ({tempPtr} to {tempPtr + block_size})", level = DEBUG)        
                return E_NOT_OK
        
        #Request transfer exit
        try:
            self.client.request_transfer_exit()
            display_message(f"!!!Transfer {section.name} exited!!!", level = DEBUG)    
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"Error while exiting transfer {section.name}", level = DEBUG)        
            return E_NOT_OK

        #validate the {section.name}
        display_message(f"Validating flashing {section.name} from {section.start_address} to {section.end_address}", level = DEBUG)
        ReqData = hex2bytes(section.start_address) + hex2bytes(section.end_address) + self.checksum_calc(fileContent)
        try:
            response = self.client.start_routine(0xFF01, ReqData)
            display_message(f"Flashing {section.name} validated", level = DEBUG)
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"{section.name} validation encounters errors", level = DEBUG)
            return E_NOT_OK

    def resetSoftware(self):
        display_message(f"Flashing completed, resetting the ECU...", level = DEBUG)
        try: 
            self.client.ecu_reset(HARDRESET)
            return E_OK
        except Exception as e:
            display_message(f"{e}", level = DEBUG)
            display_message(f"Cannot reset ECU", level = DEBUG)
            return E_NOT_OK

    def flash(self):
        retVal_u8 = E_NOT_OK
        
        # Unlock ECU
        retVal_u8 = self.unlockECU(self.client)

        if retVal_u8 == E_NOT_OK:
            display_message("Not able to unlock ECU...", level=DEBUG)
            return E_NOT_OK
            
        for section in self.flash_sections:
            retVal_u8 = self.flashSection(section)
            if retVal_u8 == E_NOT_OK:
                display_message("FATAL ERROR WHILE FLASHING {section}", level=DEBUG)
                return E_NOT_OK

        return E_OK

    def run(self):
        flash_status = self.flash()
        if flash_status == E_OK:
            ecuResetStatus = self.resetSoftware(client)
            if ecuResetStatus == E_OK:
                display_message(f"Flashing completed with success.", level = DEBUG)
        else:
            display_message(f"Flashing unsuccessful with error, please see the logs above...", level = DEBUG)
        return E_NOT_OK
