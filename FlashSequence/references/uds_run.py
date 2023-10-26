from can.interfaces.socketcan import SocketcanBus
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.services import *
import udsoncan
import isotp

# Refer to isotp documentation for full details about parameters
isotp_params = {
     'stmin'                       : 32,    # Will request the sender to wait 32ms between consecutive frame. 0-127ms or 100-900ns with values from 0xF1-0xF9
     'blocksize'                   : 8,     # Request the sender to send 8 consecutives frames before sending a new flow control message
     'wftmax'                      : 0,     # Number of wait frame allowed before triggering an error
     'tx_data_length'              : 8,     # Link layer (CAN layer) works with 8 byte payload (CAN 2.0)
   #'tx_data_min_length'           : None,  # Minimum length of CAN messages. When different from None, messages are padded to meet this length. Works with CAN 2.0 and CAN FD.
     'tx_data_min_length'          : 8,
     'tx_padding'                  : 0,     # Will pad all transmitted CAN messages with byte 0x00.
     'rx_flowcontrol_timeout'      : 1000,  # Triggers a timeout if a flow control is awaited for more than 1000 milliseconds
     'rx_consecutive_frame_timeout': 1000,  # Triggers a timeout if a consecutive frame is awaited for more than 1000 milliseconds
     'squash_stmin_requirement'    : False, # When sending,                                             respect the stmin requirement of the receiver. If set to True, go as fast as possible.
     'max_frame_size'              : 4095                # Limit the size of receive frame.
}

bus     = SocketcanBus(channel='can0')                                          # Link Layer (CAN protocol)
tp_addr = isotp.Address(isotp.AddressingMode.NormalFixed_29bits, source_address=0xFA, target_address = 0x00) # Network layer addressing scheme
stack   = isotp.CanStack(bus=bus, address=tp_addr)               # Network/Transport layer (IsoTP protocol)
stack.set_sleep_timing(0, 0)     
                                                   # Speed First (do not sleep)
conn      = PythonIsoTpConnection(stack)
didlist   = [0xF201]
didconfig = {0xF201: '22s'}                                             # interface between Application and Transport layer


with Client(conn, request_timeout=1) as client:                                     # Application layer (UDS protocol)
   
   # SID 10
   response = client.change_session(3)
   print(response)
   
   # SID 22 
   #request = ReadDataByIdentifier.make_request(didlist,didconfig)   
   request = ReadDataByIdentifier.make_request(0xF201,didconfig) 
   response = client.send_request(request)

   data = ReadDataByIdentifier.ResponseData(response)
   data = response.get_payload()
   
   #data = ReadDataByIdentifier.interpret_response(response,didlist = didlist, didconfig = didconfig)   
   
   
   # Tester present
   # response = client.tester_present()
   
   # Request Download - SID 34
   
   address = 0x800009FF
   memorysize = 0x100
   response = client.request_download(udsoncan.MemoryLocation(address, memorysize))
   
   
   # SID 31
   
   a = 0  
   for i in range(0xF000,0xFFFF):
       
       try:
           request = RoutineControl.make_request(i, control_type = 0x01, data=None)
           response = client.send_request(request)
           print("RID = " + i)
           break
       except:
           a = a + 1
           if (a > 1000):
               break
   
   
   # SID 2E
   
   request = WriteDataByIdentifier.make_request(0xF201,bytes([0x00, 0x01, 0x02, 0x03, 0x04]),didconfig)  
   response = client.send_request(request)
   
   
   
   #SID_27
   
   level    = 3
   response = client.request_seed(level)
   data     = response.get_payload()
   
   print("Length seed = " + str(len(data)))
   print("Seed = ")
   for i in range(2,6):
       print(hex(data[i]))
       
   key = b'Hell'
   response = client.send_key(level, key)
   
   
   #SID 36
   
   sequence_number = 0
   data_flashing = b'0123456789987654322323'
   response = client.transfer_data(sequence_number, data=data_flashing)
   
   
   #SID 37
   
   response = client.request_transfer_exit(data=None)
   
   
   #Read bin file then send to ECU 
   
   with open('random_bin_file.bin', 'rb') as file:
  
      first_128_bytes = file.read(128)
      print("First 128 bytes:", first_128_bytes)
  
  
      next_128_bytes = file.read(128)
      print("Next 128 bytes:", next_128_bytes)
   try:
      response = client.transfer_data(sequence_number = 0, data=first_128_bytes)
   except:
      a = 0
   response = client.transfer_data(sequence_number = 1, data=next_128_bytes)
   
   

   print(response)
   print(hex(data[0]))
   print(response.data)
   print(response.code_name)
   print(response.code)
   #
   

