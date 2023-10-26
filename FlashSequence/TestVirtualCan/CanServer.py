import can

bus1 = can.interface.Bus('test', bustype='virtual')
bus2 = can.interface.Bus('test', bustype='virtual')

while True:
    msg1 = can.Message(arbitration_id=0xabcde, data=[1,2,3])
    bus1.send(msg1)
    msg2 = bus2.recv()

#assert msg1                == msg2
assert  msg1.arbitration_id == msg2.arbitration_id
assert  msg1.data           == msg2.data
assert  msg1.timestamp      != msg2.timestamp