#!/usr/bin/python
"""Test general health of the fonts."""

import glob
import unittest

from fontTools import ttLib
from nototools import coverage
from nototools import font_data

import layout

def load_fonts():
    """Load all major fonts."""
    all_font_files = (glob.glob('out/RobotoTTF/*.ttf')
                      + glob.glob('out/RobotoCondensedTTF/*.ttf'))
    all_fonts = [ttLib.TTFont(font) for font in all_font_files]
    assert len(all_font_files) == 18
    return all_font_files, all_fonts


class TestItalicAngle(unittest.TestCase):
    """Test the italic angle of fonts."""

    def setUp(self):
        _, self.fonts = load_fonts()

    def test_italic_angle(self):
        """Tests the italic angle of fonts to be correct."""
        for font in self.fonts:
            post_table = font['post']
            if 'Italic' in font_data.font_name(font):
                expected_angle = -12.0
            else:
                expected_angle = 0.0
            self.assertEqual(post_table.italicAngle, expected_angle)


class TestMetaInfo(unittest.TestCase):
    """Test various meta information."""

    def setUp(self):
        _, self.fonts = load_fonts()

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


class TestDigitWidths(unittest.TestCase):
    """Tests the width of digits."""

    def setUp(self):
        _, self.fonts = load_fonts()
        self.digits = [
            'zero', 'one', 'two', 'three', 'four',
            'five', 'six', 'seven', 'eight', 'nine']

    def test_digit_widths(self):
        """Tests all decimal digits to make sure they have the same width."""
        for font in self.fonts:
            hmtx_table = font['hmtx']
            widths = [hmtx_table[digit][0] for digit in self.digits]
            self.assertEqual(len(set(widths)), 1)


class TestCharacterCoverage(unittest.TestCase):
    """Tests character coverage."""

    def setUp(self):
        _, self.fonts = load_fonts()
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


class TestLigatures(unittest.TestCase):
    """Tests formation or lack of formation of ligatures."""

    def setUp(self):
        self.fontfiles, _ = load_fonts()

    def test_lack_of_ff_ligature(self):
        """Tests that the ff ligature is not formed by default."""
        for fontfile in self.fontfiles:
            advances = layout.get_advances('ff', fontfile)
            self.assertEqual(len(advances), 2)


if __name__ == '__main__':
    unittest.main()

