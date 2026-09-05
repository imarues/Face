#!/usr/bin/env python3
import argparse, pathlib, struct, shutil, hashlib

MH_MAGIC_64 = 0xfeedfacf
LC_ID_DYLIB = 0x0d


def patch_id(path, new_name):
    data = bytearray(path.read_bytes())
    if len(data) < 32 or struct.unpack_from('<I', data, 0)[0] != MH_MAGIC_64:
        raise RuntimeError('Expected thin arm64 Mach-O dylib')
    ncmds = struct.unpack_from('<I', data, 16)[0]
    off = 32
    patched = False
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', data, off)
        if cmd == LC_ID_DYLIB:
            name_off = struct.unpack_from('<I', data, off + 8)[0]
            start = off + name_off
            end_limit = off + cmdsize
            end = data.find(b'\0', start, end_limit)
            if end < 0:
                end = end_limit
            current = bytes(data[start:end]).decode('utf-8', 'replace')
            nb = new_name.encode('utf-8')
            capacity = end_limit - start
            if len(nb) + 1 > capacity:
                raise RuntimeError(f'New install name is too long for existing command ({current})')
            data[start:end_limit] = nb + b'\0' * (capacity - len(nb))
            patched = True
            break
        if cmdsize < 8 or off + cmdsize > len(data):
            raise RuntimeError('Malformed Mach-O load command')
        off += cmdsize
    if not patched:
        raise RuntimeError('LC_ID_DYLIB not found')
    path.write_bytes(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    a = ap.parse_args()
    src, dst = pathlib.Path(a.input), pathlib.Path(a.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    patch_id(dst, '@executable_path/CydiaSubstrate.dylib')
    print('runtime sha256:', hashlib.sha256(dst.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
