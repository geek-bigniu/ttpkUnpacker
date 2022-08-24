def zfill_bytes(data, size):
    fill_size = size - len(data)
    if fill_size > 0:
        data += b'\x00' * fill_size
    return data
