#!/usr/bin/env python
'''
facewall - Make a wall from a bunch of small avatars

LICENSE
======

facewall is licensed under MIT license
http://www.opensource.org/licenses/mit-license.php
'''

import sys, glob, os
import Image
from random import choice, sample
import collections

COLORSPACE_FILE = 'colorspace.txt'

def get_colorvector(fn):
    '''Get average color vector (r, g, b)
    '''
    im = Image.open(fn)
    im = im.convert('RGB')
    # color histogram the length should be 256 * 3
    hist = im.histogram()
    sum_cnt = 0
    sum_r = 0
    sum_g = 0
    sum_b = 0
    
    for c, cnt in enumerate(hist[:256]):
        sum_cnt += cnt
        sum_r += c * cnt

    for c, cnt in enumerate(hist[256:512]):
        sum_g += c * cnt
    
    for c, cnt in enumerate(hist[512:]):
        sum_b += c * cnt
        
    w, h = im.size
    return w, h, sum_r / sum_cnt, sum_g / sum_cnt, sum_b / sum_cnt

def gather_all_colorspace(cfn):
    colorfile = open(cfn, 'w')
    asize = None
    for fn in glob.glob('palette/*.jpg'):
        w, h, r, g, b = get_colorvector(fn)
        if asize is None:
            asize = (w, h)
        assert asize == (w, h), 'palette images must have the same size, %s' % fn
        print >>colorfile, w, h, r, g, b, fn
    colorfile.close()

def coarse(r, g, b):
    'Coarse with a larger level'
    return int(r)>>6, int(g)>>6, int(b)>>6
    #return int(r)>>5, int(g)>>5, int(b)>>5

def coarse_l(r, g, b):
    'Coarse with a larger level'
    return int(r)>>7, int(g)>>7, int(b)>>7

def read_colorspace(fn):
    ghist = collections.defaultdict(list)
    ghist_l = collections.defaultdict(list)
    f = open(fn)
    w, h = 48, 48
    for line in f.xreadlines():
        w, h, r, g, b, fn = line.split()
        c = coarse(r, g, b)
        ghist[c].append(fn)
        cl = coarse_l(r, g, b)
        ghist_l[cl].append(fn)
    f.close()
    return int(w), int(h), ghist, ghist_l

def read_template(tfn):
    im = Image.open(tfn)
    im = im.convert('RGB')
    w, h = im.size
    p = im.load()
    gl = []
    for y in xrange(h):
        row = []
        for x in xrange(w):
            r, g, b = p[x, y]
            c = coarse(r, g, b)
            cl = coarse_l(r, g, b)
            row.append((c, cl))
        gl.append(row)
    return w, h, gl

def merge(template_file, grayfile):
    w, h, template = read_template(template_file)
    pw, ph, ghist, ghist_l = read_colorspace(grayfile)
    merged = {}
    matrix = []
    fallback_file_choices = [choice(ghist[choice(ghist.keys())]) for _ in xrange(20)]
    for y in xrange(h):
        fl = []
        for x in xrange(w):
            c, cl = template[y][x]

            file_choices = ghist.get(c)
            if not file_choices:
                file_choices = ghist_l.get(cl)

            if not file_choices:
                file_choices = fallback_file_choices
            fl.append(choice(file_choices))
        matrix.append(fl)

    destimg = Image.new('RGB', (w * pw, h * ph))
    for y in xrange(h):
        for x in xrange(w):
            fn = matrix[y][x]
            im = Image.open(fn)
            destimg.paste(im, (x * pw, y * ph))
    destimg.save('wall.jpg')
    return matrix

def usage():
    print >>sys.stderr, 'Usage: %s prepare|[template.png]' % sys.argv[0]
    print >>sys.stderr, 'Options:'
    print >>sys.stderr, ' prepare: prepare colorspace file.'
    print >>sys.stderr, ' [templateimage] the template image to be put to wall.'

if __name__ == '__main__':
    if sys.argv[1:2] == ['prepare']:
        gather_all_colorspace(COLORSPACE_FILE)
    else:
        template_file = 'template.png'
        if len(sys.argv) >= 2:
            template_file = sys.argv[1]
        
        if not os.path.exists(template_file):
            print >>sys.stderr, 'Template image does not exist!'
            usage()
            sys.exit()
        elif not os.path.exists(COLORSPACE_FILE):
            print >>sys.stderr, 'Colorspace file does not exist! you need to prepare one by running "%s prepare' % sys.argv[0]
            usage()
            sys.exit()
        matrix = merge(template_file, COLORSPACE_FILE)
