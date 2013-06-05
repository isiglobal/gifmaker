#!/usr/bin/env python

"""
Gifmaker: Convert video files into gif animations. There are
options to control output framerate, reverse playback, output
size, and more. The jpeg intermediate frames that are created
during processing are not cleaned up by default so that any
of the frames may be chosen as a higher-quality still.

Note: Adjust the output framerate to control the file size and
timing.

Requires ImageMagick and ffmpeg!

	See	`./gifmaker.py --help` for usage info.

Copyright 2013 Brandon Thomas <bt@brand.io>
"""

# TODO: Arbitrary temporary directory via argument
# TODO: Resize without cropping (options: border, disobey strict 
#		dimensions, etc)
# TODO: Option to cleanup (perhaps make default, too...)
# TODO: Utilize temporary filesystem /tmp

import os
import re
import sys
import glob
import shutil
import argparse
import subprocess

TEMP_DIR = 'frame-output'

class TempDir(object):
	"""
	Temporary Directory Management
	"""
	tempdir = os.path.join(os.getcwd(), TEMP_DIR)

	@classmethod
	def wildcard(cls, extension):
		return os.path.join(cls.tempdir, '*.%s' % extension)

	@classmethod
	def target(cls, extension, i=False):
		if type(i) == bool:
			return os.path.join(cls.tempdir, '%%05d.%s' % extension)
		return os.path.join(cls.tempdir, '%05d.%s' % (i, extension))

	@classmethod
	def make(cls):
		"""Make the temporary directory."""
		print 'Make tempdir...'
		cmd = 'mkdir %s' % cls.tempdir
		with open(os.devnull, 'w') as devnull:
			r = subprocess.call(cmd, shell=True, stderr=devnull)

	@classmethod
	def cleanup(cls):
		"""Cleanup the temorary directory of all files."""
		print 'Cleanup tempdir...'
		cmd1 = 'rm %s' % cls.wildcard('jpg')
		cmd2 = 'rm %s' % cls.wildcard('gif')
		cmd3 = 'rm %s' % cls.wildcard('miff')
		with open(os.devnull, 'w') as devnull:
			r = subprocess.call(cmd1, shell=True, stderr=devnull)
			r = subprocess.call(cmd2, shell=True, stderr=devnull)
			r = subprocess.call(cmd3, shell=True, stderr=devnull)

def natsort_keys(string):
	"""
	Sort numbers naturally.
	Python should really implement this, damnit.
	http://stackoverflow.com/a/5967539
	"""
	def atoi(string):
		return int(string) if string.isdigit() else string
	return [atoi(x) for x in re.split('(\d+)', string)]

def video_get_fps(filename):
	cmd = 'ffmpeg -i %s' % filename
	regx = '(\d+\.?\d+?) fps'
	out, err = subprocess.Popen(cmd, shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE).communicate()

	# ffmpeg outputs to stderr if no output file specified
	info = out if out else err

	fps = re.findall(regx, info)
	if not fps:
		return False

	return float(fps[0])

def convert_vid_to_jpegs(filename, framerate=False):
	"""Convert the mpeg to a sequence of JPEG images."""
	print 'Convert to JPEGs...'
	cmd = 'ffmpeg -i "%s" "%s"' % (filename, TempDir.target('jpg'))
	if framerate:
		cmd = 'ffmpeg -i "%s" -r %d "%s"' % (filename, framerate,
				TempDir.target('jpg'))

	with open(os.devnull, 'w') as devnull:
		r = subprocess.call(cmd, shell=True, stderr=devnull)

def copy_jpeg_sequence_in_reverse():
	"""Copy a JPEG sequence, reverse it, append it."""
	print "Append reversed JPEG sequence..."
	files = glob.glob(TempDir.wildcard('jpg'))
	files.sort(key=natsort_keys)

	num = len(files)
	i = num*2

	for f in files[1:-1]:
		shutil.copyfile(f, TempDir.target('jpg', i))
		i -= 1

def delete_frames(num):
	"""Remove one frame for every X many."""
	print "Deleting 1 in every %d frames..." % num
	files = glob.glob(TempDir.wildcard('jpg'))
	files.sort(key=natsort_keys)

	i = 0
	while i < len(files):
		fn = files[i]
		if i % num == 0:
			os.remove(fn)
		i += 1

def resize_jpegs(width, height, gravity='Center', quality=100):
	"""Resize the jpegs to specified dimenions."""
	cmd1 ='mogrify -quality %d -resize %dx%d %s' % (
			quality, 1200, height, TempDir.wildcard('jpg'))
	cmd2 ='mogrify -quality %d -gravity %s -crop %dx%d+0+0 %s' % (
			quality, gravity, width, height, TempDir.wildcard('jpg'))
	print 'Resize JPEGs...'
	r = subprocess.call(cmd1, shell=True)
	print 'Crop JPEGs...'
	r = subprocess.call(cmd2, shell=True)

def convert_jpegs_to_gifs():
	"""Convert JPEG frames into gif frames."""
	print 'Convert JPEGs to GIFs...'
	cmd = 'convert %s %s' % (
		TempDir.wildcard('jpg'), TempDir.target('miff'))
	r = subprocess.call(cmd, shell=True)

def assemble_animated_gif(filename, delay=0):
	"""Assemble gif frames into final animated gif."""
	print 'Assemble animated GIF...'
	cmd = 'convert -delay %d -loop 0 %s %s' % (
			delay, TempDir.wildcard('miff'), filename)
	r = subprocess.call(cmd, shell=True)

def request_args():
	"""Setup and parse commandline args."""

	def process_dimensions(string):
		dims = string.split('x')
		if len(dims) < 2:
			dims.append(dims[0])

		return {
			'width': int(dims[0]),
			'height': int(dims[1])
		}

	parser = argparse.ArgumentParser(
			description='Convert an mp4 clip into a gif image.')

	parser.add_argument('-r', '--reverse', dest='reverse',
					action='store_true',
					required=False,
					default=False,
					help='Append reversed playback for easy looping.')

	parser.add_argument('-f', '--framerate', dest='framerate',
					action='store',
					metavar='FPS',
					type=int,
					default=0,
					help='Specify the output framerate.')

	parser.add_argument('-d', '--delay', dest='delay',
					action='store',
					metavar='DELAY',
					type=int,
					default=0,
					help='Specify the gif animation delay. Default '
						'is no delay. See also: output fps (-r).')

	parser.add_argument('-s', '--size', dest='size',
					action='store',
					metavar='DIMENSION',
					required=True,
					help='Size as WxH or simply W for \'square\'')

	parser.add_argument('-g', '--gravity', dest='gravity',
					action='store',
					metavar='GRAVITY',
					required=False,
					default='Center',
					choices = [
						'NorthWest', 'North', 'NorthEast',
						'West', 'Center', 'East',
						'SouthWest', 'South', 'SouthEast',
					],
					help='If cropped, gravity may be: NorthWest, '
						+ 'North, NorthEast, West, Center, East, '
						+ 'SouthWest, South, SouthEast. Center is '
						+ 'default.')

	parser.add_argument('input',
					action='store',
					metavar='SOURCE',
					help='mp4 input filename')

	parser.add_argument('output',
					action='store',
					metavar='DEST',
					help='gif output filename')

	args = parser.parse_args()

	dims = process_dimensions(args.size)
	args.width = dims['width']
	args.height = dims['height']

	args.input = os.path.realpath(os.path.expanduser(args.input))

	return args

def main():
	"""
	Main program!
	"""
	args = request_args()

	TempDir.make()
	TempDir.cleanup()

	convert_vid_to_jpegs(args.input, args.framerate)

	if args.reverse:
		copy_jpeg_sequence_in_reverse()

	resize_jpegs(args.width, args.height, gravity=args.gravity)

	convert_jpegs_to_gifs()

	assemble_animated_gif(args.output, delay=args.delay)

	print 'DONE!'

if __name__ == '__main__':
	main()

