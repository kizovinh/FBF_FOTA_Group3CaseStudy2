from clsCodeSection import CodeSection

DEFAULT_SESSION              = 0x01
PROGRAMMING_SESSION          = 0x02
EXTENDED_SESSION             = 0x03
SUPPLIER_PROGRAMMING_SESSION = 0x61

E_OK     = 0
E_NOT_OK = 1

DCM_SEC_LEVEL_1_2 = 1

NUM_BYTES_FLASH = 0x0180

BOOTCTRL_START_ADDR = 0x80000000
BOOTCTRL_END_ADDR   = 0x8000FFFF
BOOTCTRL_SIZE       = 0x00010000

ASW0_START_ADDR = 0x80080000
ASW0_END_ADDR   = 0x8023FFFF
ASW0_SIZE       = 0x001C0000

ASW1_START_ADDR = 0x80340000
ASW1_END_ADDR   = 0x805FFFFF
ASW1_SIZE       = 0x002C0000

ASW2_START_ADDR = 0x00000000
ASW2_END_ADDR   = 0x00000000
ASW2_SIZE       = 0x00000000

DS0_START_ADDR = 0x80240000
DS0_END_ADDR   = 0x8033FFFF
DS0_SIZE       = 0x00100000

VDS_START_ADDR = 0x00000000
VDS_END_ADDR   = 0x00000000
VDS_SIZE       = 0x00000000

CB_START_ADDR = 0x80050000
CB_END_ADDR   = 0x8007FFFF
CB_SIZE       = 0x00030000

RESERVED_START_ADDR = 0x00000000
RESERVED_END_ADDR   = 0x00000000
RESERVED_SIZE       = 0x00000000

HARDRESET     = 1
KEYOFFONRESET = 2
SOFTRESET     = 3

TESTER_ADDR = 0xFA
ECU_ADDR    = 0x00

FLASH_USING_SPLITTED_HEX_FILE   = 1
FLASH_USING_SINGLE_HEX_FILE     = 2
FLASH_USING_BIN_FILE            = 3
FLASH_USING_COMPRESSED_BIN_FILE = 4

oBootCtrl   = CodeSection(BOOTCTRL_START_ADDR, BOOTCTRL_END_ADDR, BOOTCTRL_SIZE, "BootCtrl")
oAsw0       = CodeSection(ASW0_START_ADDR, ASW0_END_ADDR, ASW0_SIZE, "ASW0")
oAsw1       = CodeSection(ASW1_START_ADDR, ASW1_END_ADDR, ASW1_SIZE, "ASW1")
oAsw2       = CodeSection(ASW2_START_ADDR, ASW2_END_ADDR, ASW2_SIZE, "ASW2")
oDs0        = CodeSection(DS0_START_ADDR, DS0_END_ADDR, DS0_SIZE, "DS0")
oVds        = CodeSection(VDS_START_ADDR, VDS_END_ADDR, VDS_SIZE, "VDS")
oCb         = CodeSection(CB_START_ADDR, CB_END_ADDR, CB_SIZE, "CB")
