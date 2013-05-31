#!/usr/bin/env python

"""
Take the input mp4 file and convert it into a gif animation
of the dimensions specified.

The jpeg intermediate frames are not cleaned up so that any
frame may be used as a still.

Requires ImageMagick and ffmpeg!

	See	`./convert.py --help` for usage info.

Copyright 2013 Brandon Thomas <bt@brand.io>
"""

# TODO: Arbitrary temporary directory
# TODO: Default resize dimensions
# TODO: Reverse not yet implemented

import os
import argparse
import subprocess

TEMP_DIR = 'frame-output'

def tempdir():
	return os.path.join(os.getcwd(), TEMP_DIR)

def make_tempdir():
	"""Make the temporary directory."""
	print 'Make tempdir...'
	cmd = 'mkdir %s' % tempdir()
	with open(os.devnull, 'w') as devnull:
		r = subprocess.call(cmd, shell=True, stderr=devnull)

def cleanup_tempdir():
	"""Cleanup the temorary directory of all files."""
	print 'Cleanup tempdir...'
	cmd = 'rm %s' % os.path.join(tempdir(), '*.jpg')
	with open(os.devnull, 'w') as devnull:
		r = subprocess.call(cmd, shell=True, stderr=devnull)

def convert_vid_to_jpegs(filename):
	"""Convert the mpeg to a sequence of JPEG images."""
	print 'Convert to JPEGs...'
	#* ffmpeg -i whatever.mp4 frames/%d.jpg
	cmd = 'ffmpeg -i %s %s' % (filename, os.path.join(tempdir(), '%d.jpg'))
	with open(os.devnull, 'w') as devnull:
		r = subprocess.call(cmd, shell=True, stderr=devnull)

def resize_jpegs(width, height, quality=100):
	"""Resize the jpegs to specified dimenions."""
	globJpg = os.path.join(tempdir(), '*.jpg')
	cmd1 = 'mogrify -quality %d -resize %dx%d %s' % (quality, 1200, height, globJpg)
	cmd2 = 'mogrify -quality %d -gravity Center -crop %dx%d+0+0 %s' % (
				quality, width, height, globJpg)
	print 'Resize JPEGs...'
	r = subprocess.call(cmd1, shell=True)
	print 'Crop JPEGs...'
	r = subprocess.call(cmd2, shell=True)


def convert_jpegs_to_gifs():
	"""Convert JPEG frames into gif frames."""
	print 'Convert JPEGs to GIFs...'
	globJpg = os.path.join(tempdir(), '*.jpg')
	outGif = os.path.join(tempdir(), '%d.miff')
	cmd = 'convert %s %s' % (globJpg, outGif)
	r = subprocess.call(cmd, shell=True)

def assemble_animated_gif(filename, delay=0):
	"""Assemble gif frames into final animated gif."""
	print 'Assemble animated GIF...'
	globGif = os.path.join(tempdir(), '*.miff')
	cmd = 'convert -delay %d -loop 0 %s %s' % (delay, globGif, filename)
	r = subprocess.call(cmd, shell=True)

def request_args():
	"""Setup and parse commandline args."""
	parser = argparse.ArgumentParser(
			description='Convert an mp4 clip into a gif image.')
	parser.add_argument('-r', '--reverse', dest='reverse',
					action='store_true',
					default=False,
					help='Append reversed playback for easy looping.')
	parser.add_argument('-s', '--size', dest='size',
					action='store',
					metavar='DIMENSION',
					required=True,
					help='Size as WxH or simply W for \'square\'')
	parser.add_argument('input',
					action='store',
					metavar='SOURCE',
					help='mp4 input filename')
	parser.add_argument('output',
					action='store',
					metavar='DEST',
					help='gif output filename')
	args = parser.parse_args()

	dims = args.size.split('x')
	if len(dims) < 2:
		dims.append(dims[0])

	width = dims[0]
	height = dims[1]

	args.width = int(width)
	args.height = int(height)

	args.input = os.path.realpath(os.path.expanduser(args.input))

	return args

def main():
	"""
	Main program!
	"""
	args = request_args()

	print args

	make_tempdir()
	cleanup_tempdir()

	convert_vid_to_jpegs(args.input)
	resize_jpegs(args.width, args.height)
	convert_jpegs_to_gifs()
	assemble_animated_gif(args.output)

	print 'DONE!'

if __name__ == '__main__':
	main()

