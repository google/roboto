# coding=UTF-8
#
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common tests for different targets."""

import glob
import unittest

from fontTools import ttLib
from nototools import coverage
from nototools import font_data

import freetype

import layout
import roboto_data


def get_rendered_char_height(font_filename, font_size, char, target='mono'):
    if target == 'mono':
        render_params = freetype.FT_LOAD_TARGET_MONO
    elif target == 'lcd':
        render_params = freetype.FT_LOAD_TARGET_LCD
    render_params |= freetype.FT_LOAD_RENDER

    face = freetype.Face(font_filename)
    face.set_char_size(font_size*64)
    face.load_char(char, render_params)
    return face.glyph.bitmap.rows


def load_fonts(patterns, expected_count=None):
    """Load all fonts specified in the patterns.

    Also assert that the number of the fonts found is exactly the same as
    expected_count."""
    all_font_files = []
    for pattern in patterns:
        all_font_files += glob.glob(pattern)
    all_fonts = [ttLib.TTFont(font) for font in all_font_files]
    if expected_count:
        assert len(all_font_files) == expected_count
    return all_font_files, all_fonts


class FontTest(unittest.TestCase):
    """Parent class for all font tests."""
    loaded_fonts = None


class TestItalicAngle(FontTest):
    """Test the italic angle of fonts."""

    def setUp(self):
        _, self.fonts = self.loaded_fonts

    def test_italic_angle(self):
        """Tests the italic angle of fonts to be correct."""
        for font in self.fonts:
            post_table = font['post']
            if 'Italic' in font_data.font_name(font):
                expected_angle = -12.0
            else:
                expected_angle = 0.0
            self.assertEqual(post_table.italicAngle, expected_angle)


class TestMetaInfo(FontTest):
    """Test various meta information."""

    def setUp(self):
        _, self.fonts = self.loaded_fonts

    def test_mac_style(self):
        """Tests the macStyle of the fonts to be correct.

        Bug: https://code.google.com/a/google.com/p/roboto/issues/detail?id=8
        """
        for font in self.fonts:
            font_name = font_data.font_name(font)
            bold = ('Bold' in font_name) or ('Black' in font_name)
            italic = 'Italic' in font_name
            expected_mac_style = (italic << 1) | bold
            self.assertEqual(font['head'].macStyle, expected_mac_style)

    def test_fs_type(self):
        """Tests the fsType of the fonts to be 0.

        fsType of 0 marks the font free for installation, embedding, etc.

        Bug: https://code.google.com/a/google.com/p/roboto/issues/detail?id=29
        """
        for font in self.fonts:
            self.assertEqual(font['OS/2'].fsType, 0)

    def test_vendor_id(self):
        """Tests the vendor ID of the fonts to be 'GOOG'."""
        for font in self.fonts:
            self.assertEqual(font['OS/2'].achVendID, 'GOOG')

    def test_us_weight(self):
        "Tests the usWeight of the fonts to be correct."""
        for font in self.fonts:
            weight = roboto_data.extract_weight_name(font_data.font_name(font))
            expected_numeric_weight = roboto_data.WEIGHTS[weight]
            self.assertEqual(
                font['OS/2'].usWeightClass,
                expected_numeric_weight)

    def test_version_numbers(self):
        "Tests the two version numbers of the font to be correct."""
        for font in self.fonts:
            build_number = roboto_data.get_build_number()
            expected_version = '2.' + build_number
            version = font_data.font_version(font)
            usable_part_of_version = version.split(';')[0]
            self.assertEqual(usable_part_of_version,
                             'Version ' + expected_version)

            revision = font_data.printable_font_revision(font, accuracy=5)
            self.assertEqual(revision, expected_version)


class TestNames(FontTest):
    """Tests various strings in the name table."""

    def setUp(self):
        _, self.fonts = self.loaded_fonts
        self.condensed_family_name = self.family_name + ' Condensed'
        self.names = []
        for font in self.fonts:
            self.names.append(font_data.get_name_records(font))

    def test_copyright(self):
        """Tests the copyright message."""
        for records in self.names:
            self.assertEqual(
                records[0],
                'Copyright 2011 Google Inc. All Rights Reserved.')

    def test_family_name(self):
        """Tests the family name."""
        for records in self.names:
            self.assertIn(records[1],
                          [self.family_name, self.condensed_family_name])
            if 16 in records:
                self.assertEqual(records[16], records[1])

    def test_postscript_name_for_spaces(self):
        """Tests that there are no spaces in PostScript names."""
        for records in self.names:
            self.assertFalse(' ' in records[6])


class TestDigitWidths(FontTest):
    """Tests the width of digits."""

    def setUp(self):
        self.font_files, self.fonts = self.loaded_fonts
        self.digits = [
            'zero', 'one', 'two', 'three', 'four',
            'five', 'six', 'seven', 'eight', 'nine']

    def test_digit_widths(self):
        """Tests all decimal digits to make sure they have the same width."""
        for font in self.fonts:
            hmtx_table = font['hmtx']
            widths = [hmtx_table[digit][0] for digit in self.digits]
            self.assertEqual(len(set(widths)), 1)

    def test_superscript_digits(self):
        """Tests that 'numr' features maps digits to Unicode superscripts."""
        ascii_digits = '0123456789'
        superscript_digits = u'⁰¹²³⁴⁵⁶⁷⁸⁹'
        for font_file in self.font_files:
            numr_glyphs = layout.get_advances(
                ascii_digits, font_file, '--features=numr')
            superscript_glyphs = layout.get_advances(
                superscript_digits, font_file)
            self.assertEqual(superscript_glyphs, numr_glyphs)


class TestCharacterCoverage(FontTest):
    """Tests character coverage."""

    def setUp(self):
        _, self.fonts = self.loaded_fonts
        self.LEGACY_PUA = frozenset({0xEE01, 0xEE02, 0xF6C3})

    def test_inclusion_of_legacy_pua(self):
        """Tests that legacy PUA characters remain in the fonts."""
        for font in self.fonts:
            charset = coverage.character_set(font)
            for char in self.LEGACY_PUA:
                self.assertIn(char, charset)

    def test_non_inclusion_of_other_pua(self):
        """Tests that there are not other PUA characters except legacy ones."""
        for font in self.fonts:
            charset = coverage.character_set(font)
            pua_chars = {
                char for char in charset
                if 0xE000 <= char <= 0xF8FF or 0xF0000 <= char <= 0x10FFFF}
            self.assertTrue(pua_chars <= self.LEGACY_PUA)

    def test_lack_of_unassigned_chars(self):
        """Tests that unassigned characters are not in the fonts."""
        for font in self.fonts:
            charset = coverage.character_set(font)
            self.assertNotIn(0x2072, charset)
            self.assertNotIn(0x2073, charset)
            self.assertNotIn(0x208F, charset)

    def test_inclusion_of_sound_recording_copyright(self):
        """Tests that sound recording copyright symbol is in the fonts."""
        for font in self.fonts:
            charset = coverage.character_set(font)
            self.assertIn(
                0x2117, charset,  # SOUND RECORDING COPYRIGHT
                'U+2117 not found in %s.' % font_data.font_name(font))


class TestLigatures(FontTest):
    """Tests formation or lack of formation of ligatures."""

    def setUp(self):
        self.fontfiles, _ = self.loaded_fonts

    def test_lack_of_ff_ligature(self):
        """Tests that the ff ligature is not formed by default."""
        for fontfile in self.fontfiles:
            advances = layout.get_advances('ff', fontfile)
            self.assertEqual(len(advances), 2)

    def test_st_ligatures(self):
        """Tests that st ligatures are formed by dlig."""
        for fontfile in self.fontfiles:
            for combination in [u'st', u'ſt']:
                normal = layout.get_glyphs(combination, fontfile)
                ligated = layout.get_glyphs(
                    combination, fontfile, '--features=dlig')
                self.assertTrue(len(normal) == 2 and len(ligated) == 1)


class TestFeatures(FontTest):
    """Tests typographic features."""

    def setUp(self):
        self.fontfiles, _ = self.loaded_fonts

    def test_smcp_coverage(self):
        """Tests that smcp is supported for our required set."""
        with open('res/smcp_requirements.txt') as smcp_reqs_file:
            smcp_reqs_lis = []
            for line in smcp_reqs_file.readlines():
                line = line[:line.index(' #')]
                smcp_reqs_list.append(unichr(int(line, 16)))

        for fontfile in self.fontfiles:
            chars_with_no_smcp = []
            for char in smcp_reqs_list:
                normal = layout.get_glyphs(char, fontfile)
                smcp = layout.get_glyphs(char, fontfile, '--features=smcp')
                if normal == smcp:
                    chars_with_no_smcp.append(char)
            self.assertEqual(
                chars_with_no_smcp, [],
                ("smcp feature is not applied to '%s'" %
                    u''.join(chars_with_no_smcp).encode('UTF-8')))


class TestVerticalMetrics(FontTest):
    """Test the vertical metrics of fonts."""

    def setUp(self):
        _, self.fonts = self.loaded_fonts

    def test_ymin_ymax(self):
        """Tests yMin and yMax to be equal to Roboto v1 values.

        Android requires this, and web fonts expect this.
        """
        for font in self.fonts:
            head_table = font['head']
            self.assertEqual(head_table.yMin, -555)
            self.assertEqual(head_table.yMax, 2163)

    def test_hhea_table_metrics(self):
        """Tests ascent, descent, and lineGap to be equal to Roboto v1 values.
        """
        for font in self.fonts:
            hhea_table = font['hhea']
            self.assertEqual(hhea_table.descent, -500)
            self.assertEqual(hhea_table.ascent, 1900)
            self.assertEqual(hhea_table.lineGap, 0)

