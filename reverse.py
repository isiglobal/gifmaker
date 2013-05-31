#!/usr/bin/env python

import glob
import shutil

import re
def natural_key(string_):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

outdir = 'duplicate'

files = glob.glob('*.jpg')
files.sort(key=natural_key)

for f in files:
	shutil.copyfile(f, outdir+'/'+f)

num = len(files)

i = num*2
for f in files:
	shutil.copyfile(f, outdir+'/'+str(i)+'.jpg')
	i-= 1

print files
