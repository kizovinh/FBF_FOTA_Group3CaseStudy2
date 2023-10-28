from ComDia import *
from UDSflash import Flash
import logging

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

    oAsw0.path = "./binInput/asw0_notCompressed.bin"
    oAsw1.path = "./binInput/asw1_notCompressed.bin"
    oDs0.path  = "./binInput/ds0_notCompressed.bin"

    flash_sections  = [oAsw0, oAsw1, oDs0]
    flash_obj       = Flash(flash_sections)
    flash_status    = flash_obj.run()

    if flash_status   == E_OK:
        logging.debug("!!!Flash completed successfully!!!")
    del flash_obj
    



