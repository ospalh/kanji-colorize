#!/usr/bin/env python
# -*- coding: utf-8 ; mode: Python -*-

# kanji-colorize.py processes KanjiVG data into colored stroke order diagrams
# Copyright © 2012 Cayenne Boyer, Roland Sieker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Usage: see README file

import os, colorsys, re

def stroke_count(svg):
    'Return the number of strokes in the svg, based on occurences of "<path "'
    return len(re.findall('<path ', svg))

def hsv_to_rgbhexcode(h, s, v):
    'Convert an h, s, v color into rgb form #000000'
    color = colorsys.hsv_to_rgb(h, s, v)
    return '#%02x%02x%02x' % tuple([i * 255 for i in color])


def contrast_generator(n, options):
    """Create an iterator that loops through n colors twice (so that they can be used
for both strokes and stroke numbers) """
    angle = 0.618033988749895 # conjugate of the golden ratio
    for i in 2 * range(n):
        yield hsv_to_rgbhexcode(i * angle, options.saturation, options.value)

def spectrum_generator(n, options):
    """Create an iterator that loops through n colors twice (so that they can be used
for both strokes and stroke numbers) """
    for i in 2 * range(n):
        yield hsv_to_rgbhexcode(float(i)/n, options.saturation, options.value)

def indexed_generator(n, options):
    """Create an iterator that loops through n colors twice (so that they can be used
for both strokes and stroke numbers) """
    stroke_color_palette = [
        "#bf0909", "#bfbf09", "#09bf09", "#09bfbf", "#0909bf", "#bf09bf",
        "#ff850c", "#85ff0c", "#0cff85", "#0c85ff", "#850cff", "#ff0c85",
        "#bf8f2f", "#5fbf2f", "#2fbf8f", "#2f5fbf", "#8f2fbf", "#bf2f5f", 
        "#ff0000", "#ffcc00", "#65ff00", "#00ff66", "#00cbff", "#0000ff",
        "#cc00ff", "#ff0066",
        "#ff6600", "#cbff00", "#00ff00", "#00ffcb", "#0066ff", "#6500ff",
        "#ff00cb"
        ]
    for i in range(n):
        m = i % len(stroke_color_palette)
        yield stroke_color_palette[m]
    for i in range(n):
        # Do the loop for 2n, as for the other modes. 
        m = i % len(stroke_color_palette)
        yield stroke_color_palette[m]


# List of modes, so that we don’t call a non-existing function.
mode_dict = {
    'spectrum' : spectrum_generator,
    'contrast' : contrast_generator,
    'indexed'  : indexed_generator
    }

def color_generator(n, options):
    """Dispatch to the right color generation iterator, using the mode
config variable to determine what colors to produce."""

    # This will fail if the script is called with an undefined mode. I
    # think that is acceptable behaviour. When we don’t understand
    # what we should do, complain.
    mode = options.mode
    if not mode:
        mode = 'spectrum'
    return mode_dict[mode](n, options)



def color_svg(svg, mode):
    "Color the svg according to the mode config variable"
    color_iterator = color_generator(stroke_count(svg), options)
    def color_match(match_object):
        return match_object.re.pattern + 'style="stroke:' + next(color_iterator) + '" '
    svg = re.sub('<path ', color_match, svg)
    return re.sub('<text ', color_match, svg)

def resize_svg(svg, options):
    "Resize the svg according to the image_size config variable"
    ratio = `float(options.size) / 109`
    svg = svg.replace('109" height="109" viewBox="0 0 109 109', '{0}" height = "{0}" viewBox="0 0 {0} {0}'.format(`options.size`))
    svg = re.sub('(<g id="kvg:Stroke.*?)(>)', r'\1 transform="scale(' + ratio + ',' + ratio + r')"\2', svg)
    return svg

def comment_copyright(svg, options):
    "Add a comment about what this script has done to the copyright notice"
    note = """This file has been modified from the original version by the kanji-colorize 
script (available at http://github.com/cayennes/kanji-colorize) with these 
settings: """
    if options.mode:
        note += """
    mode: """+ options.mode
    note += """
    saturation: """ + `options.saturation` + """
    value: """ + `options.value` + """
    size: """ + `options.size` + """
It remains under a Creative Commons-Attribution-Share Alike 3.0 License.

The original SVG has the following copyright:

"""
    place_before = "Copyright (C)"
    return svg.replace(place_before, note + place_before)

def convert_file_name(filename):
    "Convert unicode code in filename to actual character"
    def hex_to_unicode_char(match_object):
        'local function used for a call to re.sub'
        return unichr(int(match_object.group(0), 16))
    return re.sub('^[0-9a-fA-F]*', hex_to_unicode_char, filename)

# Find and set up directories

def kanji_dirs(in_dir=u'', out_dir=u'', mode=u''):
    """Find the KanjiVG directory"""
    if not in_dir:
        if (os.path.exists('kanji')):
            in_dir = 'kanji'
        elif (os.path.exists(os.path.join('kanjivg', 'kanji'))):
            in_dir = os.path.join('kanjivg', 'kanji')
        elif (os.path.exists(os.path.join(os.path.pardir,'kanjivg','kanji'))):
            in_dir = os.path.join(os.path.pardir,'kanjivg','kanji')
        else:
            # Last resort: use current directory.
            in_dir = u'.'
    if not out_dir:
        out_dir = 'kanji-colorize'
        if mode:
            out_dir += '-' + mode
    if not (os.path.exists(out_dir)):
        os.mkdir(out_dir)
    return in_dir, out_dir
   
# Do conversions

def convert_all_kanji(options):
    """Colorize all SVG by coloring the strokes of KanjiVG SVG files"""
    src_dir, dst_dir = kanji_dirs(options.in_dir, options.out_dir,
                                  options.mode)
    for src_filename in os.listdir(src_dir):
    # read original svg
        with open(os.path.join(src_dir, src_filename), 'r') as f:
            svg = f.read()
        # modify
        svg = color_svg(svg, options)
        svg = resize_svg(svg, options)
        svg = comment_copyright(svg, options)
        # write to new svg
        dst_filename = src_filename
        if options.rename:
            dst_filename = convert_file_name(src_filename)
        
        with open(os.path.join(dst_dir, dst_filename), 'w') as f:
            f.write(svg)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-i", "--in-dir", dest="in_dir",
                      help="Directory where the KanjiVG svg files are stored",
                      metavar="INDIR")
    parser.add_option("-o", "--out-dir", dest="out_dir",
                      help="Directory where the colorized kanji are written to. Default is to use kanji-colorize-<MODE>",
                      metavar="OUTDIR")
    parser.add_option("-c", "--colors",
                      dest="mode",
                      help='Color selection mode. Use "spectrum" or "contrast"')
    parser.add_option("--saturation",
                      dest="saturation", default=0.95, type="float",
                      help='Saturation of the strokes')
    parser.add_option("--value",
                      dest="value", default=0.75, type="float",
                      help='Value of the strokes')
    parser.add_option("-s", "--size",
                      dest="size", default=327, type="int",
                      help='Svg standard size.')
    parser.add_option("--no-rename",
                      dest="rename", action="store_false",
                      help='Keep the ascii character names. Usual behaviour is to change the output file names to the characters themselves.')
    parser.add_option("--rename",
                      dest="rename", action="store_true",
                      help='Change the output file names to the characters themselves. This is the default behaviour.')
    (options, args) = parser.parse_args()
    if None == options.rename:
        options.rename = True
    if args:
        print 'Warning: arguments "' + args + '" are ignored.'
    convert_all_kanji(options)
