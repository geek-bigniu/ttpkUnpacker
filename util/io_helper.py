import struct

from util import common


class IOHelper:
    @staticmethod
    def read_struct(io, fmt, zfill=True):
        struct_size = struct.calcsize(fmt)
        data = io.read(struct_size)

        if zfill:
            data = common.zfill_bytes(data, struct_size)
        elif len(data) == 0:
            return None

        result = struct.unpack(fmt, data)
        return result

    @staticmethod
    def read_ascii_string(io, max_size=-1, ignore_zero=False):
        result = ''
        zero_break = not ignore_zero and max_size != -1

        while max_size == -1 or len(result) < max_size:
            [char] = IOHelper.read_struct(io, 'B')
            if char == 0 and zero_break:
                break

            result += chr(char)
        return result

    @staticmethod
    def read_range(io, offset=0, size=-1):
        io.seek(offset)
        return io.read(size)

    @staticmethod
    def write_struct(io, fmt, *values):
        data = struct.pack(fmt, *values)
        return io.write(data)

    @staticmethod
    def write_ascii_string(io, content: str):
        data = content.encode('ascii') + b'\x00'
        return io.write(data)
