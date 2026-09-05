#!/usr/bin/env python3
import sys, struct, pathlib
MH_MAGIC_64=0xfeedfacf; LC_SEGMENT_64=0x19
for arg in sys.argv[1:]:
 p=pathlib.Path(arg); d=p.read_bytes()
 if len(d)<32 or struct.unpack_from('<I',d,0)[0]!=MH_MAGIC_64: raise SystemExit(f'{p}: not thin arm64 Mach-O64')
 cputype=struct.unpack_from('<I',d,4)[0]
 filetype=struct.unpack_from('<I',d,12)[0]
 if cputype!=0x0100000c: raise SystemExit(f'{p}: not ARM64 cputype')
 if filetype!=6: raise SystemExit(f'{p}: not MH_DYLIB (filetype={filetype})')
 ncmds=struct.unpack_from('<I',d,16)[0]; off=32; init=[]
 for _ in range(ncmds):
  cmd,cmdsize=struct.unpack_from('<II',d,off)
  if cmd==LC_SEGMENT_64:
   nsects=struct.unpack_from('<I',d,off+64)[0]; s0=off+72
   for i in range(nsects):
    s=s0+i*80; sect=d[s:s+16].split(b'\0',1)[0].decode(); flags=struct.unpack_from('<I',d,s+64)[0]
    if sect in ('__init_offsets','__mod_init_func'): init.append((sect,flags&0xff))
  off+=cmdsize
 print(f'{p.name}: ARM64 DYLIB initializer_sections={init}')
