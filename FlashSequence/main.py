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

from clsCodeSection import CodeSection


if __name__ == "__main__":
    oAsw0.path = "./binInput/asw0_notCompressed.bin"
    oAsw1.path = "./binInput/asw1_notCompressed.bin"
    oDs0.path = "./binInput/ds0_notCompressed.bin"
    flash_sections = [oAsw0, oAsw1, oDs0]
    flash_obj = Flash()
    flash_status = flash_obj.run()
    if flash_status == E_OK:
        print(" Flash OKKK")
    del flash_obj
    



