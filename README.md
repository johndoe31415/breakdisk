# breakdisk
breakdisk is a tool to test around specific locations of a disk. It operates by
reading the original block contents, then writing a random pattern to the same
location, reading back that random pattern and re-writing the original
contents.  For a working disk, this therefore *should* not alter the disk
contents, but you should use extreme caution around to tool and assume that
it'll simply overwrite all contents with random garbage. Usage:

# Usage
```
$ ./breakdisk.py --help
usage: breakdisk.py [-h] [-o pos] [-r range] [-b size] [--no-align] [-v]
                    [--i-know-what-im-doing]
                    blockdev

positional arguments:
  blockdev              Device that should be overwritten.

optional arguments:
  -h, --help            show this help message and exit
  -o pos, --origin pos  The origin location inside the disk at which to start
                        testing. When given as an integer value, corresponds
                        to a value in bytes. Can also have suffixes 'M', 'G',
                        'T', 'Mi', 'Gi', 'Ti', 's', 'p' or '%' to give the
                        value in Megabytes (10^6), Gigabytes (10^9), Terabytes
                        (10^12), Mebibytes (2^20), Gibibytes (2^30), Tebibytes
                        (2^40), sectors (512 bytes), pages (4096 bytes) or a
                        percentage relative to the disk size, respectively.
                        Defaults to 0.
  -r range, --testrange range
                        Relative to the origin, gives the range of testing
                        that occurs in the device. Can be prefixed with '+' or
                        '~' to indicate only moving forward or backward from
                        the origin, otherwise moves in both directions. Can
                        have any of the suffixes valid for origin. Defaults to
                        "+100%".
  -b size, --blocksize size
                        Block size in bytes. Defaults to 1048576.
  --no-align            Do not align minimum and maximum position at
                        blocksize.
  -v, --verbose         Show some more detailed output.
  --i-know-what-im-doing
                        Disables any warnings or questions that would prevent
                        you from accidently making a terrible, irreversible
                        mistake.
```

For example, let's say you receive dmesg warnings that with a particular disk
`/dev/sdx`, there's errors around a specific sector. The messages might look
like this:

```
[11745.840393] sd 7:0:0:0: [sdx] tag#21 FAILED Result: hostbyte=DID_BAD_TARGET driverbyte=DRIVER_OK
[11745.840394] sd 7:0:0:0: [sdx] tag#21 CDB: Write(10) 2a 00 ad 43 c5 40 00 05 40 00
[11745.840395] print_req_error: I/O error, dev sdx, sector 2906899776
```

Then you want to test the disk exactly at that location to see if it was a
fluke. Note that if something's wrong with the disk, this usually will worsen
the condition significantly and cause the whole disk to fall apart. Hence the
name of the tool.

If you, for example, wan to have an area of +-100 MiB to be tested around
sector 2906899776, you could (as root) do the following:

```
# ./breakdisk.py --origin 2906899776s --testrange 100Mi /dev/sdx
Disk size: 1500301910016 bytes (1.50 TB)
Content of disk /dev/sdx (1.50 TB) WILL BE DESTROYED
Are you sure (type 'YES' to confirm)? YES
Origin at 1488332685312 bytes (1.49 TB), testrange +-104857600 bytes (105 MB).
Range: 1488227139584 to 1488437903360 bytes (1.49 TB to 1.49 TB) - length 210763776 bytes (211 MB)
Processing 201 blocks.
0.0%: Testing offset 1488227139584 / 0x15a81400000 (1.49 TB)
0.5%: Testing offset 1488228188160 / 0x15a81500000 (1.49 TB)
1.0%: Testing offset 1488229236736 / 0x15a81600000 (1.49 TB)
1.5%: Testing offset 1488230285312 / 0x15a81700000 (1.49 TB)
2.0%: Testing offset 1488231333888 / 0x15a81800000 (1.49 TB)
2.5%: Testing offset 1488232382464 / 0x15a81900000 (1.49 TB)
[...]
98.0%: Testing offset 1488433709056 / 0x15a8d900000 (1.49 TB)
98.5%: Testing offset 1488434757632 / 0x15a8da00000 (1.49 TB)
99.0%: Testing offset 1488435806208 / 0x15a8db00000 (1.49 TB)
99.5%: Testing offset 1488436854784 / 0x15a8dc00000 (1.49 TB)
Testing finished successfully, no errors reported.
```

## Dependencies
breakdisk requires Python3.

## License
GNU GPL-3.
