import nfc
from contextlib import contextmanager

_connstring = 'pn532_uart:/dev/ttyS0'
_target_type = nfc.NMT_ISO14443B
_nbr = nfc.NBR_106

@contextmanager
def nfc_open(connstring=_connstring):
    """Open the PN532 for reading.

    Use this like so:
    with reader.nfc_open() as pnd:
        do_stuff_with_pnd(pnd)
    
    Automatically takes care of closing the connection for you.
    """
    ctx = nfc.init()
    if ctx is None:
        raise RuntimeError('Couldn\'t init libnfc')

    pnd = nfc.open(ctx, connstring)
    if pnd is None:
        raise IOError('Couldn\'t open NFC device')

    try:
        if nfc.initiator_init(pnd) < 0:
            raise IOError('Couldn\'t init NFC device')
        
        print('Opened NFC reader device on {}'.format(
            nfc.device_get_name(pnd)
        ))

        yield pnd
    finally:
        # cleanup...
        nfc.close(pnd)
        nfc.exit(ctx)

def block_for_card(target_type=_target_type, nbr=_nbr):
    """Block (wait) until a card is detected, then return its info.
    """
    with nfc_open() as pnd:
        modul = nfc.modulation()
        modul.nmt = target_type
        modul.nbr = nbr
        target = nfc.target()

        print('Now waiting for a target.')
        # this blocks
        retval = nfc.initiator_select_passive_target(
            pnd, modul, 0, 0, target
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
    print_hex(target.nti.nai.abtUid, pre='UID: ')

    return target