"""Interface code to read a CAN from a CEPAS card.
"""

import nfc
from contextlib import contextmanager

_connstring = 'pn532_uart:/dev/ttyS0'
_target_type = nfc.NMT_ISO14443B
_nbr = nfc.NBR_106

# command bytes to select stuff
_cmd_select_mf = bytes.fromhex('00 a4 00 00 02 3f 00 00')
_cmd_select_ef = bytes.fromhex('00 a4 00 00 02 40 00 00')
_cmd_read_purse = bytes.fromhex('90 32 03 00 00 3f')

class NFCSession():
    """Represents an NFC session between a reader device and an NFC tag.
    """
    pass

@contextmanager
def nfc_open(connstring=_connstring):
    """Open the PN532 for reading.

    Use this like so:
    with reader.nfc_open() as device:
        do_stuff_with_device(device)
    
    Automatically takes care of closing the connection for you.

    Fun fact: you can (and should) do this with regular file open() as well. 
    """
    ctx = nfc.init()
    if ctx is None:
        raise RuntimeError('Couldn\'t init libnfc')

    device = nfc.open(ctx, connstring)
    if device is None:
        raise IOError('Couldn\'t open NFC device')

    try:
        if nfc.initiator_init(device) < 0:
            raise IOError('Couldn\'t init NFC device')
        
        print('Opened NFC reader device on {}'.format(
            nfc.device_get_name(device)
        ))

        yield device
    finally:
        # cleanup...
        nfc.close(device)
        nfc.exit(ctx)

def block_for_card(device, target_type=_target_type, nbr=_nbr):
    """Block (wait) until a card is detected, then return its info.
    """
    modul = nfc.modulation()
    modul.nmt = target_type
    modul.nbr = nbr
    target = nfc.target()

    print('Now waiting for a target.')
    # this blocks
    retval = nfc.initiator_select_passive_target(
        device, modul, 0, 0, target
    )

    print('Got something. retval={}'.format(retval))
    return target

def print_hex(bstr, pre=None, post=None):
    if pre is not None:
        print(pre, end='')

    bstr = bytes(bstr)
    nfc.print_hex(bstr, len(bstr))

    if post is not None:
        print(post)
    else:
        print()

def inspect_target(target):
    """Inspect a target (returns the same target)
    """
    # this UID is NOT unique
    print_hex(target.nti.nai.abtUid, pre='UID: ')

    return target

def transceive(device, transmit, timeout=1000):
    """Transmit data to the tag, then receive a response. Waits until timeout (in ms) is reached
    """
    tx = bytes(transmit)
    tx_len = len(tx)
    rx_len = 1024
    retval, rx = nfc.initiator_transceive_bytes(device, tx, tx_len, rx_len, timeout)
    if retval != len(rx):
        raise IOError('transceive: retval and rx length mismatch (error transceiving?)', {
            'retval': retval,
            'rx': rx
        })
    return rx 

def cepas_read_purse(device):
    """Read the purse data from a presented CEPAS card.
    """
    # select the master file
    rx = transceive(device, _cmd_select_mf)
    print_hex(rx, pre='CEPAS: select_mf response: ')

    # select the elementary file
    rx = transceive(device, _cmd_select_ef)
    print_hex(rx, pre='CEPAS: select_ef response: ')

    # read the purse
    rx = transceive(device, _cmd_read_purse)
    print_hex(rx, pre='CEPAS: read_purse response: ')

    return rx

def main():
    with nfc_open() as device:
        target = inspect_target(block_for_card(device))
        purse = cepas_read_purse(device)
        # print_hex(rx, pre='CEPAS: read_purse response: ')

if __name__ == '__main__':
    main()