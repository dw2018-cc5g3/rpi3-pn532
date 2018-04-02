"""Interface code to read a CAN from a CEPAS card.

Quick start:

    import reader
    can = reader.block_for_can()
    print('Your CAN: {}'.format(can))

block_for_can() accepts 1 optional argument to control whether spaces are 
inserted (default is true):

    import reader
    can = reader.block_for_can(spaces=False)
    insert_into_db(can, ...)

You must install dependencies first (see README.md).
"""

import nfc
from contextlib import contextmanager
from binascii import hexlify

_connstring = 'pn532_uart:/dev/ttyS0'
_target_type = nfc.NMT_ISO14443B
_nbr = nfc.NBR_106

# command bytes to select stuff
_cmd_select_mf = bytes.fromhex('00 a4 00 00 02 3f 00 00')
_cmd_select_ef = bytes.fromhex('00 a4 00 00 02 40 00 00')
_cmd_read_purse = bytes.fromhex('90 32 03 00 00 3f')

class NFCError(IOError):
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
        raise NFCError('Couldn\'t open NFC device', {
            'connstring': connstring
        })

    try:
        if nfc.initiator_init(device) < 0:
            raise NFCError('Couldn\'t init NFC device', {
                'connstring': connstring
            })
        
        print('Opened NFC reader device on {}'.format(
            nfc.device_get_name(device)
        ))

        yield device
    finally:
        # cleanup...
        nfc.close(device)
        nfc.exit(ctx)

def block_for_card(device, target_type=None, nbr=None):
    """Block (wait) until a card is detected, then return its info.
    """
    modul = nfc.modulation()
    modul.nmt = target_type if target_type is not None else _target_type
    modul.nbr = nbr if nbr is not None else _nbr
    target = nfc.target()

    # this blocks
    retval = nfc.initiator_select_passive_target(
        device, modul, 0, 0, target
    )

    if not retval:
        raise NFCError('Couldn\'t establish initial connection with card', {
            'retval': retval,
            'target_type': modul.nmt,
            'nbr': modul.nbr
        })

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
    """Transmit data to the tag, then receive a response. Waits until timeout
    (in ms) is reached
    """
    tx = bytes(transmit)
    tx_len = len(tx)
    rx_max_len = 256
    rx_len, rx = nfc.initiator_transceive_bytes(
        device, tx, tx_len, rx_max_len, timeout)

    if rx_len < 0:
        # failed
        raise NFCError('initiator_transceive_bytes failed', {
            'retval': rx_len
            })

    return rx 

def cepas_read_purse(device):
    """Read the purse data from a presented CEPAS card.
    """
    # select the master file
    rx = transceive(device, _cmd_select_mf)

    # select the elementary file
    rx = transceive(device, _cmd_select_ef)

    # read the purse
    rx = transceive(device, _cmd_read_purse)
    
    return rx

def cepas_extract_can(purse_data, spaces=True):
    """Extract the CAN from the raw byte sequence of the purse data.
    """
    can_bytes_raw = purse_data[8:16]
    can_str_raw = hexlify(can_bytes_raw).decode('utf-8')
    assert len(can_str_raw) == 16

    if spaces:
        # split every 4 characters
        return ' '.join(can_str_raw[i*4:(i+1)*4] for i in range(4))
    else:
        return can_str_raw

def block_for_can(spaces=True):
    """Acquire the libnfc context, open the reader, wait for a suitable card,
    extract a CAN, then finally close the reader and release the context. All
    automatic!!! 
    """
    with nfc_open() as device:
        # wait for a card to present
        block_for_card(device)
        can = cepas_extract_can(cepas_read_purse(device), spaces)
    
    return can

def main():
    print('Tap a CEPAS card...')
    try:
        print('Your CAN: {}'.format(block_for_can()))
    except NFCError as e:
        print('NFC error occurred!')
        try:
            if e.args[1].get('retval') == nfc.NFC_ERFTRANS:
                print('RF transmission error. Did you remove ' \
                    'the card too quickly?')
        except IndexError:
            pass
        
        print('repr: {}'.format(repr(e)))

if __name__ == '__main__':
    main()