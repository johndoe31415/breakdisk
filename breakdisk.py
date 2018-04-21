#!/usr/bin/python3
#	breakdisk - Test block devices at specific disk locations
#	Copyright (C) 2018-2018 Johannes Bauer
#
#	This file is part of breakdisk.
#
#	breakdisk is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	breakdisk is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import sys
import collections
import argparse

from FriendlyArgumentParser import FriendlyArgumentParser
from FilesizeFormatter import FilesizeFormatter

_Position = collections.namedtuple("Position", [ "value", "suffix" ])
_Deviation = collections.namedtuple("Deviation", [ "direction", "position" ])

class BlockTester(object):
	def __init__(self, args, fd):
		self._args = args
		self._fd = fd
		self._lastblock = None

	def _rndblock(self, length):
		if (self._lastblock is None) or (len(self._lastblock) != length):
			self._lastblock = os.urandom(length)
		return self._lastblock

	def test(self, offset, length):
		success = True

		os.lseek(self._fd, offset, os.SEEK_SET)
		original = os.read(self._fd, length)
		if len(original) != length:
			raise Exception("Tried to read %d bytes at offset %d, but got %d." % (length, offset, len(original)))
		rnd = self._rndblock(length)

		os.lseek(self._fd, offset, os.SEEK_SET)
		os.write(self._fd, rnd)

		os.lseek(self._fd, offset, os.SEEK_SET)
		readback = os.read(self._fd, length)
		if readback != rnd:
			success = False

		os.lseek(self._fd, offset, os.SEEK_SET)
		os.write(self._fd, original)
		return success

def _arg_position(text):
	suffixes = {
		"M":	1000 * 1000,
		"G":	1000 * 1000 * 1000,
		"T":	1000 * 1000 * 1000 * 1000,
		"Mi":	1024 * 1024,
		"Gi":	1024 * 1024 * 1024,
		"Ti":	1024 * 1024 * 1024 * 1024,
		"s":	512,
		"p":	4096,
		"%":	1,
	}
	found_suffix = None
	found_coeff = 1
	value = text
	for (suffix, coeff) in suffixes.items():
		if value.endswith(suffix):
			found_suffix = suffix
			found_coeff = coeff
			value = value[:-len(suffix)].strip()
			break

	try:
		numvalue = int(value)
	except ValueError:
		try:
			numvalue = float(value)
		except ValueError:
			raise argparse.ArgumentTypeError("\"%s\" is not a valid numeric value." % (value))
	return _Position(value = numvalue * found_coeff, suffix = found_suffix)

def _arg_testrange(text):
	text = text.strip()
	if text.startswith("+"):
		direction = "+"
		text = text[1:]
	elif text.startswith("-") or text.startswith("~"):
		direction = "-"
		text = text[1:]
	else:
		direction = "+-"
	return _Deviation(direction = direction, position = _arg_position(text))

def determine_disksize(blockdev):
	with open(blockdev, "rb") as f:
		f.seek(0, os.SEEK_END)
		return f.tell()

def interpret_position(position, disksize):
	if position.suffix == "%":
		return round(position.value * disksize / 100)
	else:
		return position.value

parser = FriendlyArgumentParser()
parser.add_argument("-o", "--origin", metavar = "pos", type = _arg_position, default = "0", help = "The origin location inside the disk at which to start testing. When given as an integer value, corresponds to a value in bytes. Can also have suffixes 'M', 'G', 'T', 'Mi', 'Gi', 'Ti', 's', 'p' or '%%' to give the value in Megabytes (10^6), Gigabytes (10^9), Terabytes (10^12), Mebibytes (2^20), Gibibytes (2^30), Tebibytes (2^40), sectors (512 bytes), pages (4096 bytes) or a percentage relative to the disk size, respectively. Defaults to %(default)s.")
parser.add_argument("-r", "--testrange", metavar = "range", type = _arg_testrange, default = "+100%", help = "Relative to the origin, gives the range of testing that occurs in the device. Can be prefixed with '+' or '~' to indicate only moving forward or backward from the origin, otherwise moves in both directions. Can have any of the suffixes valid for origin. Defaults to \"%(default)s\".")
parser.add_argument("-b", "--blocksize", metavar = "size", type = int, default = 1024 * 1024, help = "Block size in bytes. Defaults to %(default)d.")
parser.add_argument("--no-align", action = "store_true", help = "Do not align minimum and maximum position at blocksize.")
parser.add_argument("-v", "--verbose", action = "store_true", help = "Show some more detailed output.")
parser.add_argument("--i-know-what-im-doing", action = "store_true", help = "Disables any warnings or questions that would prevent you from accidently making a terrible, irreversible mistake.")
parser.add_argument("blockdev", metavar = "blockdev", type = str, help = "Device that should be overwritten.")
args = parser.parse_args(sys.argv[1:])

fsfmt = FilesizeFormatter()
disksize_bytes = determine_disksize(args.blockdev)
if disksize_bytes == 0:
	raise Exception("Determination of disk size failed or disk has size zero.")

if args.verbose:
	print("Disk size: %d bytes (%s)" % (disksize_bytes, fsfmt(disksize_bytes)), file = sys.stderr)

if not args.i_know_what_im_doing:
	print("Content of disk %s (%s) WILL BE DESTROYED" % (args.blockdev, fsfmt(disksize_bytes)), file = sys.stderr)
	response = input("Are you sure (type 'YES' to confirm)? ")
	if response != "YES":
		print("Aborted process, nothing was written.", file = sys.stderr)
		sys.exit(1)

origin = interpret_position(args.origin, disksize_bytes)
testrange = interpret_position(args.testrange.position, disksize_bytes)
if args.verbose:
	print("Origin at %d bytes (%s), testrange %s%d bytes (%s)." % (origin, fsfmt(origin), args.testrange.direction, testrange, fsfmt(testrange)), file = sys.stderr)

if args.testrange.direction == "-":
	range_min = max(origin - testrange, 0)
	range_max = min(origin, disksize_bytes)
elif args.testrange.direction == "+":
	range_min = max(origin, 0)
	range_max = min(origin + testrange, disksize_bytes)
elif args.testrange.direction == "+-":
	range_min = max(origin - testrange, 0)
	range_max = min(origin + testrange, disksize_bytes)
else:
	raise Exception(NotImplemented, "Origin direction %s" % (args.testrange.direction))

if not args.no_align:
	range_min = range_min // args.blocksize * args.blocksize
	range_max = (range_max + args.blocksize - 1) // args.blocksize * args.blocksize

range_size = range_max - range_min
if args.verbose:
	print("Range: %d to %d bytes (%s to %s) - length %d bytes (%s)" % (range_min, range_max, fsfmt(range_min), fsfmt(range_max), range_size, fsfmt(range_size)), file = sys.stderr)

block_count = (range_size + args.blocksize - 1) // args.blocksize
if args.verbose:
	print("Processing %d blocks." % (block_count), file = sys.stderr)

try:
	fdid = os.open(args.blockdev, flags = os.O_RDWR | os.O_SYNC)
	tester = BlockTester(args, fdid)
	for blockid in range(block_count):
		start = range_min + (blockid * args.blocksize)
		end = range_min + ((blockid + 1) * args.blocksize)
		end = min(end, range_max)
		length = end - start
		if args.verbose:
			percent_done = blockid / block_count * 100
			print("%.1f%%: Testing offset %d / 0x%x (%s)" % (percent_done, start, start, fsfmt(start)))
		if not tester.test(start, length):
			raise Exception("Deviation at offset %d (%s): Cannot guarantee integrity of original content, block readback failed." % (start, fsfmt(start)))
finally:
	os.close(fdid)
if args.verbose:
	print("Testing finished successfully, no errors reported.", file = sys.stderr)
