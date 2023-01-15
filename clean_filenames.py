#! /usr/local/bin/python3

import os
import re
import sys

class CharacterTranslator(object):

  def __init__(self, ccdict_path=None):
    self.translations = { }
    self.ccdict_translations = { }
    if ccdict_path:
      self.translations.update(self.get_ccdict_translations(ccdict_path))
    self.translations.update({
      chr(0x003A) : '_',  # colon (HFS path separator)
      chr(0x00C4) : 'AE', # umlaut A
      chr(0x00D6) : 'OE', # umlaut O
      chr(0x00DC) : 'UE', # umlaut U
      chr(0x00E1) : 'a',  # accute a
      chr(0x00E4) : 'ae', # umlaut a
      chr(0x00E7) : 'c',  # cedilla c
      chr(0x00E8) : 'e',  # grave e
      chr(0x00E9) : 'e',  # accute e
      chr(0x00EF) : 'i',  # umlaut i
      chr(0x00F3) : 'o',  # accute o
      chr(0x00F4) : 'o',  # circumflex o
      chr(0x00F6) : 'oe', # umlaut o
      chr(0x00FC) : 'ue', # umlaut u
      chr(0x00B0) : 'd',  # degree
      chr(0x00BF) : '',   # inverted question mark
      chr(0x00C6) : 'AE', # latin AE
      chr(0x00D8) : 'O',  # O with stroke
      chr(0x00DF) : 'ss', # sharp S
      chr(0x00E6) : 'ae', # latin ae
      chr(0x00F8) : 'o',  # o with stroke
      chr(0x0159) : 'r',  # caron r
      chr(0x0300) : '',   # grave accent
      chr(0x0301) : '',   # accute accent
      chr(0x0302) : '',   # circumflex
      chr(0x0303) : '',   # tilde
      chr(0x0306) : '',   # breve
      chr(0x0308) : 'e',  # umlaut
      chr(0x030A) : '',   # ring above
      chr(0x030C) : '',   # caron
      chr(0x0327) : '',   # cedilla
      chr(0x0430) : 'a',  # cyrillic
      chr(0x0431) : 'b',  # cyrillic
      chr(0x0432) : 'v',  # cyrillic
      chr(0x0433) : 'g',  # cyrillic
      chr(0x0434) : 'd',  # cyrillic
      chr(0x0435) : 'ie', # cyrillic
      chr(0x0436) : 'zh', # cyrillic
      chr(0x0437) : 'z',  # cyrillic
      chr(0x0438) : 'i',  # cyrillic
      chr(0x0439) : 'i',  # cyrillic
      chr(0x043A) : 'k',  # cyrillic
      chr(0x043B) : 'l',  # cyrillic
      chr(0x043C) : 'm',  # cyrillic
      chr(0x043D) : 'n',  # cyrillic
      chr(0x043E) : 'o',  # cyrillic
      chr(0x043F) : 'p',  # cyrillic
      chr(0x0440) : 'r',  # cyrillic
      chr(0x0441) : 's',  # cyrillic
      chr(0x0442) : 't',  # cyrillic
      chr(0x0443) : 'y',  # cyrillic
      chr(0x0444) : 'f',  # cyrillic
      chr(0x0445) : 'x',  # cyrillic
      chr(0x0446) : 'ts', # cyrillic
      chr(0x0447) : 'ch', # cyrillic
      chr(0x0448) : 'sh', # cyrillic
      chr(0x0449) : '',   # cyrillic
      chr(0x044A) : '',   # cyrillic
      chr(0x044B) : 'ui', # cyrillic
      chr(0x044C) : '',   # cyrillic
      chr(0x044D) : 'e',  # cyrillic
      chr(0x044E) : 'io', # cyrillic
      chr(0x044F) : 'ya', # cyrillic
      chr(0x2013) : '-',  # en dash
      chr(0x2014) : '-',  # em dash
      chr(0x3068) : '&',  # japanese
      chr(0x4E0B) : 'xia', # chinese TODO: ccdict??
      chr(0xFF08) : '(',  # fullwidth paren
      chr(0xFF09) : ')',  # fullwidth paren
      chr(0xFF0D) : '-',  # fullwidth dash
      chr(0xFF1A) : '_',  # fullwidth colon
    })

  PINYIN_SEP = '-'

  def get_ccdict_translations(self, ccdict_path):
    translations = { }
    mandarin_re = re.compile('U\+([0-9A-F]+)\.0\tfMandarin\t([a-z]*)')
    if os.path.isdir(ccdict_path):
      ccdict_path = os.path.join(ccdict_path, "ccdict.txt")
    print("Loading Mandarin translations from %s" % ccdict_path, file=sys.stderr)
    for line in open(ccdict_path, encoding="latin-1"):
      match = mandarin_re.match(line)
      if match:
        code = int(match.group(1), 16)
        pinyin = match.group(2)
        translations[chr(code)] = pinyin + self.PINYIN_SEP
    return translations

  def is_pinyin(self, c):
    return len(c) > 1 and c[-1] == self.PINYIN_SEP

  def translate_str(self, s):
    translated_chars = [self.translate_char(c, s) for c in s]
    prev = ''
    for i, c in enumerate(translated_chars):
      if self.is_pinyin(prev) and not self.is_pinyin(c):
        translated_chars[i-1] = translated_chars[i-1][:-1]
      prev = c
    return str.join('', translated_chars)

  def translate_char(self, c, s=None):
    if c in self.translations:
      return self.translations[c]
    code = ord(c)
    if code > 0x80:
      print("Unknown character: '%s' (0x%X)" % (chr(code), code), file=sys.stderr)
      if s: print("in %s" % s, file=sys.stderr)
      return '(%X)' % code
    return c


class FilenameCleaner(object):
  def __init__(self, ccdict_path=None, dry_run=False):
    self.translator = CharacterTranslator(ccdict_path=ccdict_path)
    self.adjacent_dash_dot_re = re.compile(r'[-_]+\.')
    self.trailing_characters_re = re.compile(r'[-_. ]+$')
    self.leading_non_word_re = re.compile(r'(\A|/)[\W]*')
    self.leading_article_re = re.compile(r'(?i)(\A|/)(THE|DER|DIE|DAS) ([^/]*)')
    self.dry_run = dry_run

  def recursive_clean(self, top):
    print("%s filenames in %s" % ("Checking" if self.dry_run else "Cleaning", top))
    for root, dirnames, filenames in os.walk(top, topdown=False):
      for name in filenames:
        self.maybe_rename(os.path.join(root, name))
      for name in dirnames:
        self.maybe_rename(os.path.join(root, name))

  def maybe_rename(self, name):
    dirname = os.path.dirname(name)
    basename = os.path.basename(name)
    renamed = self.clean_name(basename)
    dry = "would " if self.dry_run else ""
    if basename != renamed:
      renamed = os.path.join(dirname, renamed)
      print("%srename: %s\n     -> %s" % (dry, name, renamed))
      if not self.dry_run:
        os.rename(name, renamed)

  def clean_name(self, name):
    root, ext = os.path.splitext(name)
    root = self.translator.translate_str(root)
    root = self.adjacent_dash_dot_re.sub(r'.', root)
    root = self.trailing_characters_re.sub(r'', root)
    root = self.leading_non_word_re.sub(r'\1', root)
    root = self.leading_article_re.sub(r'\1\3, \2', root)
    return root + ext


def main():
  my_dir = os.path.dirname(sys.argv[0])
  dry_run = len(sys.argv) < 3 or sys.argv[2] != "-f"
  cleaner = FilenameCleaner(ccdict_path=my_dir, dry_run=dry_run)
  cleaner.recursive_clean(sys.argv[1])

if __name__ == "__main__":
  main()
