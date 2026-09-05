#!/usr/bin/env python3
import argparse, struct, pathlib, shutil, hashlib

MH_MAGIC_64 = 0xfeedfacf
LC_SEGMENT_64 = 0x19
LC_LOAD_DYLIB = 0x0c
LC_LOAD_WEAK_DYLIB = 0x80000018
S_REGULAR = 0x0
S_INIT_FUNC_OFFSETS = 0x16
S_MOD_INIT_FUNC_POINTERS = 0x9


def cstr16(b):
    return b.split(b'\0', 1)[0].decode('ascii', 'replace')


def patch_sections(path):
    data = bytearray(path.read_bytes())
    if len(data) < 32 or struct.unpack_from('<I', data, 0)[0] != MH_MAGIC_64:
        raise RuntimeError(f'{path.name}: expected thin 64-bit little-endian Mach-O')
    ncmds = struct.unpack_from('<I', data, 16)[0]
    off = 32
    found = []
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', data, off)
        if cmdsize < 8 or off + cmdsize > len(data):
            raise RuntimeError(f'{path.name}: malformed load command')
        if cmd == LC_SEGMENT_64:
            nsects = struct.unpack_from('<I', data, off + 64)[0]
            sec_off = off + 72
            for i in range(nsects):
                s = sec_off + i * 80
                sect = cstr16(data[s:s+16]); seg = cstr16(data[s+16:s+32])
                flags = struct.unpack_from('<I', data, s + 64)[0]
                typ = flags & 0xff
                if sect in ('__init_offsets', '__mod_init_func'):
                    if typ not in (S_INIT_FUNC_OFFSETS, S_MOD_INIT_FUNC_POINTERS, S_REGULAR):
                        raise RuntimeError(f'{path.name}: unexpected {seg},{sect} type 0x{typ:x}')
                    struct.pack_into('<I', data, s + 64, (flags & ~0xff) | S_REGULAR)
                    size = struct.unpack_from('<Q', data, s + 40)[0]
                    found.append((seg, sect, typ, size))
        off += cmdsize
    if not found:
        raise RuntimeError(f'{path.name}: no initializer section found')
    path.write_bytes(data)
    return found


def patch_dylib_path(path, old_name, new_name):
    data = bytearray(path.read_bytes())
    old_b = old_name.encode(); new_b = new_name.encode()
    if len(new_b) > len(old_b):
        raise RuntimeError('replacement path too long')
    ncmds = struct.unpack_from('<I', data, 16)[0]
    off = 32; patched = 0
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', data, off)
        if cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB) and cmdsize >= 24:
            name_off = struct.unpack_from('<I', data, off + 8)[0]
            start = off + name_off; end_limit = off + cmdsize
            end = data.find(b'\0', start, end_limit)
            if end < 0: end = end_limit
            if bytes(data[start:end]) == old_b:
                capacity = end_limit - start
                data[start:end_limit] = new_b + b'\0' * (capacity - len(new_b))
                patched += 1
        off += cmdsize
    if patched == 0:
        raise RuntimeError(f'{path.name}: CydiaSubstrate dependency not found')
    path.write_bytes(data)
    return patched


def neutralize_wolf_analytics_category(path):
    """Neutralize Wolf's non-lazy Firebase UIViewController analytics +load.
    The category still exists in the ordinary Objective-C category list, but
    the runtime no longer auto-runs its +load while Wolf is supposed to be OFF.
    """
    data = bytearray(path.read_bytes())
    if len(data) < 32 or struct.unpack_from('<I', data, 0)[0] != MH_MAGIC_64:
        raise RuntimeError(f'{path.name}: expected thin 64-bit little-endian Mach-O')
    ncmds = struct.unpack_from('<I', data, 16)[0]
    off = 32
    changed = 0
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', data, off)
        if cmd == LC_SEGMENT_64:
            nsects = struct.unpack_from('<I', data, off + 64)[0]
            sec_off = off + 72
            for i in range(nsects):
                s = sec_off + i * 80
                sect = cstr16(data[s:s+16])
                if sect == '__objc_nlcatlist':
                    new = b'__mf_nlcatlist'
                    data[s:s+16] = new + b'\0' * (16 - len(new))
                    changed += 1
        off += cmdsize
    if changed:
        path.write_bytes(data)
    return changed


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-dir', required=True)
    ap.add_argument('--output-dir', required=True)
    a = ap.parse_args()
    src = pathlib.Path(a.input_dir); out = pathlib.Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in ('iQFace.dylib', 'Glow.dylib', 'Wolf.dylib'):
        s = src / name; d = out / name
        if not s.exists(): raise SystemExit(f'Missing {s}')
        shutil.copy2(s, d)
        print(name, 'substrate path patches:', patch_dylib_path(
            d,
            '@rpath/CydiaSubstrate.framework/CydiaSubstrate',
            '@executable_path/CydiaSubstrate.dylib'))
        print(name, 'initializer sections:', patch_sections(d))
        if name == 'Wolf.dylib':
            print(name, 'neutralized non-lazy analytics categories:', neutralize_wolf_analytics_category(d))
        print(name, 'sha256:', sha(d))

if __name__ == '__main__':
    main()
