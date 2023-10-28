from ComDia import *
from clsCodeSection import CodeSection

import logging

from can.interfaces.socketcan import SocketcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.configs import ClientConfig
from udsoncan.services import *
import isotp
import udsoncan
import time

class Flash:
    def __init__(self, flash_sections: list[CodeSection]):
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
        tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid = TESTER_ADDR, rxid = ECU_ADDR)  # Network layer addressing scheme

        # Network/Transport layer (IsoTP protocol)
        self.stack = isotp.CanStack(bus=bus, address=tp_addr , params = isotp_params)
        
        # Speed First (do not sleep)
        self.stack.set_sleep_timing(0, 0)

        client_cfg = ClientConfig(
            use_server_timing        = False,
            p2_star_timeout          = 4.0,
            p2_timeout               = 4.0,
            security_algo            = self.algoSeca,
            security_algo_params     = {},
            server_memorysize_format = 32,
            server_address_format    = 32,
            request_timeout          = None
            )
        self.conn = PythonIsoTpConnection(self.stack)
        self.client = Client(self.conn, config = client_cfg)
        self.flash_sections = flash_sections
        
    def readBinFile(filePath) -> bytes:
        try:
            with open(filePath, 'rb') as file:
                buffer    = file.read()
                file_size = len(buffer)

                logging.debug(f"File Size: {file_size} bytes")

                return buffer

        except FileNotFoundError:
            logging.debug(f"File not found: {filePath}")
            return E_NOT_OK
        except Exception as e:
            logging.debug(f"Error: {e}")
            return E_NOT_OK

    def hex2bytes(hexNum) -> bytes:
        byte_data = bytes.fromhex(format(hexNum, 'X'))
        return byte_data

    def unlockECU(self):
        retVal_u8 = E_OK

        #Check Tester Connection
        logging.debug("Changing Session to DEFAULT SESSION...")
        try:
            response = self.client.change_session(DEFAULT_SESSION)
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug("Cannot change session to DEFAULT SESSION...")
            return E_NOT_OK
            
        logging.debug("!!!ECU is in DEFAULT SESSION!!!")

        #Changing Session to SUPPLIER PROGRAMMING SESSION
        logging.debug("Requesting SUPPLIER PROGRAMMING SESSION SESSION...")
        try: 
            response = self.client.change_session(SUPPLIER_PROGRAMMING_SESSION)
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug("Cannot change session to SUPPLIER PROGRAMMING SESSION...")
            return E_NOT_OK
        logging.debug("ECU is in SUPPLIER_PROGRAMMING_SESSION!!!")
        
        time.sleep(1)
        #Changing Session to PROGRAMMING SESSION
        logging.debug("Requesting PROGRAMMING SESSION...")
        try:
            response = self.client.change_session(PROGRAMMING_SESSION)
            logging.debug("ECU is in PROGRAMMING SESSION DONE")
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug("Cannot change session to PROGRAMMING SESSION...")
            return E_NOT_OK

        #Unlock Security
        logging.debug("Accessing ECU's security...")
        try:
            response = self.client.unlock_security_access(DCM_SEC_LEVEL_1_2)
            logging.debug("ECU's security accessed")
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug("Cannot access ECU's security")
            return E_NOT_OK

        return retVal_u8

    # Dummy SID 27 SEED-KEY algorithm
    def algoSeca(level: int, seed : bytes, params : dict) ->  bytes:
        keys = bytes([0 ,0 ,0 ,0])
        return keys

    # Calculate checksum
    def caculateChecksum(fileContent) -> bytes:
        chkSum = sum (fileContent) & 0xFFFF
        return bytes([(chkSum & 0xFF00) >> 8, chkSum & 0xFF])
             
    def flashSection(self, section: CodeSection):
        fileContent = self.readBinFile(section.path)

        ####################################   {section.name}    ######################################
        logging.debug(f"Flashing {section.name} section...")

        #Erase {section.name}
        logging.debug(f"{section.name} section from {section.start_address} to {section.end_address} will be erased ...")
        ReqData = self.hex2bytes(section.start_address) + self.hex2bytes(section.end_address)
        try:
            response = self.client.start_routine( 0xFF00, ReqData)
            logging.debug(f"Request erase {section.name} successful...")
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug(f"Request erase {section.name} unsuccessful !")
            return E_NOT_OK

        #Request Download
        logging.debug(f"Requesting for download {section.name}...")
        ReqData = udsoncan.MemoryLocation(section.start_address, section.size)
        try:
            response = self.client.request_download(ReqData)
            logging.debug(f"Requested for download {section.name} successful")
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug(f"Requested for download {section.name} unsuccessful!!!")
            return E_NOT_OK
        
        #Transfer Data
        logging.debug(f"Start flashing {section.name}...")

        binFileSize     = len(fileContent)
        numBlockToFlash = int(int(binFileSize) / int(NUM_BYTES_FLASH))
        lastBlockSize   = binFileSize % NUM_BYTES_FLASH
        tempPtr         = 0

        logging.debug("Bin file size will be flashed:" + str(binFileSize))
        logging.debug("Num bytes flash " + str(NUM_BYTES_FLASH))
        logging.debug("Number Block to Flash " + str(numBlockToFlash))
        logging.debug("LastBLIK SIZE " + str(lastBlockSize))
        
        for blkId in range(1, numBlockToFlash + 2):
            block_size = lastBlockSize if tempPtr >= (binFileSize - lastBlockSize) else NUM_BYTES_FLASH
            try:
                response  = self.client.transfer_data( (blkId&0xFF), fileContent[tempPtr : tempPtr + block_size])
                tempPtr  += block_size
            except Exception as e:
                logging.debug(f"{e}")
                logging.debug(f"Error while flashing {section.name} ({tempPtr} to {tempPtr + block_size})")        
                return E_NOT_OK
        
        #Request transfer exit
        try:
            self.client.request_transfer_exit()
            logging.debug(f"!!!Transfer {section.name} exited!!!")    
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug(f"Error while exiting transfer {section.name}")        
            return E_NOT_OK

        #validate the {section.name}
        logging.debug(f"Validating flashing {section.name} from {section.start_address} to {section.end_address}")
        ReqData = self.hex2bytes(section.start_address) + self.hex2bytes(section.end_address) + self.caculateChecksum(fileContent)
        try:
            response = self.client.start_routine(0xFF01, ReqData)
            logging.debug(f"Flashing {section.name} validated")
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug(f"{section.name} validation encounters errors")
            return E_NOT_OK

    def resetSoftware(self):
        logging.debug(f"Flashing completed, resetting the ECU...")
        try: 
            self.client.ecu_reset(HARDRESET)
            return E_OK
        except Exception as e:
            logging.debug(f"{e}")
            logging.debug(f"Cannot reset ECU")
            return E_NOT_OK

    def flash(self):
        retVal_u8 = E_NOT_OK
        
        # Unlock ECU
        retVal_u8 = self.unlockECU(self.client)

        if retVal_u8 == E_NOT_OK:
            logging.debug("Not able to unlock ECU...")
            return E_NOT_OK
            
        for section in self.flash_sections:
            retVal_u8 = self.flashSection(section)
            if retVal_u8 == E_NOT_OK:
                logging.debug("FATAL ERROR WHILE FLASHING {section}")
                return E_NOT_OK

        return E_OK

    def run(self):
        flash_status = self.flash()
        if flash_status == E_OK:
            ecuResetStatus = self.resetSoftware(self.client)
            if ecuResetStatus == E_OK:
                logging.debug(f"Flashing completed with success.")
        else:
            logging.debug(f"Flashing unsuccessful with error, please see the logs above...")
        return E_NOT_OK
