from kizoDebug import *
from ComDia import *
import FlashBeyondFuture

from can.interfaces.socketcan import SocketcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.configs import ClientConfig
from udsoncan.services import *
import isotp
import time
import sys

from clsCodeSection import CodeSection


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

    client_cfg1 = ClientConfig(
        use_server_timing        = False,
        p2_star_timeout          = 4.0,
        p2_timeout               = 4.0,
        security_algo            = FlashBeyondFuture.Algo_Seca,
        security_algo_params     = {},
        server_memorysize_format = 32,
        server_address_format    = 32
        )
    
    conn = PythonIsoTpConnection(stack)
    
    with Client(conn, config = client_cfg1 ,request_timeout = None) as client:
        #FLASH_USING_SINGLE_HEX_FILE FLASH_USING_BIN_FILE
        try:
            flashResult = FlashBeyondFuture.flash(client, FLASH_USING_BIN_FILE)
            if flashResult == E_OK:
                FlashBeyondFuture.resetSoftware(client)
                print_write_file(f"Flash successful...", level = DEBUG)
                sys.exit(0)
            else:
                print_write_file(f"Flash unsuccessful hihi, please see the logs above...", level = DEBUG)
        except Exception as e:
            print_write_file(f"Flash unsuccessful, please see the logs above...", level = DEBUG)
            sys.exit(1)



