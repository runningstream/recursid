from typing import Union

def convert_bytes_to_str(indat: Union[bytes, str]):
    """
    Convert bytes to a python string in a standard way

    This should only be used for purposes of outputting data to screen or
    other string-only data output, because it may be difficult or impossible
    to change back into bytes for output to a file or other...

    This is useful if you want to make sure an object is always handled as
    string, perhaps if it can come from a byte source or another string,
    like when picking a URL out of either text entry, JSON file (string only),
    or downloaded file (bytes).  You can use this to ensure proper string
    handling at the sacrifice of converting byte data to a non-byte format.
    """
    try:
        outdat = indat.decode("utf-8", errors="backslashreplace")
    except AttributeError as e:
        outdat = indat
    return outdat
