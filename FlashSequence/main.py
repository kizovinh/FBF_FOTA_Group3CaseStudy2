from ComDia import *
import UDSflash

from can.interfaces.socketcan import SocketcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.configs import ClientConfig
from udsoncan.services import *
import isotp
import time
import logging

from clsCodeSection import CodeSection


if __name__ == "__main__":
    #Config for logging 
    logging.basicConfig(
        level    = logging.DEBUG,
        format   = '[%(asctime)s] - %(levelname)-8s : %(message)s',
        handlers = [
            logging.FileHandler('./FlashSequence/project.log'),
            logging.StreamHandler()
        ]
    )
    
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
    bus      = SocketcanBus(channel='can0')
    tp_addr  = isotp.Address(isotp.AddressingMode.Normal_11bits, txid = TESTER_ADDR, rxid = ECU_ADDR)  # Network layer addressing scheme

    # Network/Transport layer (IsoTP protocol)
    stack = isotp.CanStack(bus = bus, address = tp_addr, params = isotp_params)
    
    # Speed First (do not sleep)
    stack.set_sleep_timing(0, 0)

    client_cfg1 = ClientConfig(
        use_server_timing        = False,
        p2_star_timeout          = 4.0,
        p2_timeout               = 4.0,
        security_algo            = UDSflash.algoSeca,
        security_algo_params     = {},
        server_memorysize_format = 32,
        server_address_format    = 32
        )
    
    conn = PythonIsoTpConnection(stack)
    
    with Client(conn, config = client_cfg1 ,request_timeout = None) as client:
        if UDSflash.flash(client, FLASH_USING_BIN_FILE) == E_OK:
            UDSflash.resetSoftware(client)
        else:
            logging.debug(f"Flash unsuccessful, please see the logs above...")



