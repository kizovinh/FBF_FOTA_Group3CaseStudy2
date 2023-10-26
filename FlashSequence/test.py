def hex2bytes(hexNum):
    try:
        byte_data = bytes.fromhex(format(hexNum, 'X'))
        return byte_data
    except ValueError as e:
        print(f"Error: {e}")
        return None

ReqData = hex2bytes(0x80080000) + hex2bytes(0x8023FFFF)

print(ReqData)