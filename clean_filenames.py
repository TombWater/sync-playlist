#! /usr/bin/python

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
      unichr(0x003A) : '_',  # colon (HFS path separator)
      unichr(0x00C4) : 'AE', # umlaut A
      unichr(0x00D6) : 'OE', # umlaut O
      unichr(0x00DC) : 'UE', # umlaut U
      unichr(0x00E1) : 'a',  # accute a
      unichr(0x00E4) : 'ae', # umlaut a
      unichr(0x00E7) : 'c',  # cedilla c
      unichr(0x00E8) : 'e',  # grave e
      unichr(0x00E9) : 'e',  # accute e
      unichr(0x00EF) : 'i',  # umlaut i
      unichr(0x00F3) : 'o',  # accute o
      unichr(0x00F4) : 'o',  # circumflex o
      unichr(0x00F6) : 'oe', # umlaut o
      unichr(0x00FC) : 'ue', # umlaut u
      unichr(0x00B0) : 'd',  # degree
      unichr(0x00BF) : '',   # inverted question mark
      unichr(0x00C6) : 'AE', # latin AE
      unichr(0x00D8) : 'O',  # O with stroke
      unichr(0x00DF) : 'ss', # sharp S
      unichr(0x00E6) : 'ae', # latin ae
      unichr(0x00F8) : 'o',  # o with stroke
      unichr(0x0159) : 'r',  # caron r
      unichr(0x0300) : '',   # grave accent
      unichr(0x0301) : '',   # accute accent
      unichr(0x0302) : '',   # circumflex
      unichr(0x0303) : '',   # tilde
      unichr(0x0306) : '',   # breve
      unichr(0x0308) : 'e',  # umlaut
      unichr(0x030A) : '',   # ring above 
      unichr(0x030C) : '',   # caron
      unichr(0x0327) : '',   # cedilla
      unichr(0x0430) : 'a',  # cyrillic
      unichr(0x0431) : 'b',  # cyrillic
      unichr(0x0432) : 'v',  # cyrillic
      unichr(0x0433) : 'g',  # cyrillic
      unichr(0x0434) : 'd',  # cyrillic
      unichr(0x0435) : 'ie', # cyrillic
      unichr(0x0436) : 'zh', # cyrillic
      unichr(0x0437) : 'z',  # cyrillic
      unichr(0x0438) : 'i',  # cyrillic
      unichr(0x0439) : 'i',  # cyrillic
      unichr(0x043A) : 'k',  # cyrillic
      unichr(0x043B) : 'l',  # cyrillic
      unichr(0x043C) : 'm',  # cyrillic
      unichr(0x043D) : 'n',  # cyrillic
      unichr(0x043E) : 'o',  # cyrillic
      unichr(0x043F) : 'p',  # cyrillic
      unichr(0x0440) : 'r',  # cyrillic
      unichr(0x0441) : 's',  # cyrillic
      unichr(0x0442) : 't',  # cyrillic
      unichr(0x0443) : 'y',  # cyrillic
      unichr(0x0444) : 'f',  # cyrillic
      unichr(0x0445) : 'x',  # cyrillic
      unichr(0x0446) : 'ts', # cyrillic
      unichr(0x0447) : 'ch', # cyrillic
      unichr(0x0448) : 'sh', # cyrillic
      unichr(0x0449) : '',   # cyrillic
      unichr(0x044A) : '',   # cyrillic
      unichr(0x044B) : 'ui', # cyrillic
      unichr(0x044C) : '',   # cyrillic
      unichr(0x044D) : 'e',  # cyrillic
      unichr(0x044E) : 'io', # cyrillic
      unichr(0x044F) : 'ya', # cyrillic
      unichr(0x2013) : '-',  # en dash
      unichr(0x2014) : '-',  # em dash
      unichr(0x3068) : '&',  # japanese
      unichr(0x4E0B) : 'xia', # chinese TODO: ccdict??
      unichr(0xFF08) : '(',  # fullwidth paren
      unichr(0xFF09) : ')',  # fullwidth paren
      unichr(0xFF0D) : '-',  # fullwidth dash
      unichr(0xFF1A) : '_',  # fullwidth colon
    })

  PINYIN_SEP = '-'

  def get_ccdict_translations(self, ccdict_path):
    translations = { }
    mandarin_re = re.compile('U\+([0-9A-F]+)\.0\tfMandarin\t([a-z]*)')
    if os.path.isdir(ccdict_path):
      ccdict_path = os.path.join(ccdict_path, "ccdict.txt")
    print >>sys.stderr, "Loading Mandarin translations from %s" % ccdict_path
    for line in open(ccdict_path):
      match = mandarin_re.match(line)
      if match:
        code = int(match.group(1), 16)
        pinyin = match.group(2)
        translations[unichr(code)] = pinyin + self.PINYIN_SEP
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
      print >> sys.stderr, "Unknown character: '%s' (0x%X)" % (unichr(code), code)
      if s: print >> sys.stderr, "in %s" % s
      return '(%X)' % code
    return c


class FilenameCleaner(object):
  def __init__(self, ccdict_path=None):
    self.translator = CharacterTranslator(ccdict_path=ccdict_path)
    self.adjacent_dash_dot_re = re.compile(r'[-_]+\.')
    self.trailing_characters_re = re.compile(r'[-_. ]+$')
    self.leading_non_word_re = re.compile(r'(\A|/)[\W]*')
    self.leading_article_re = re.compile(r'(?i)(\A|/)(THE|DER|DIE|DAS) ([^/]*)')

  def recursive_clean(self, top):
    for root, dirnames, filenames in os.walk(top, topdown=False):
      for name in filenames:
        self.maybe_rename(os.path.join(root, name))
      for name in dirnames:
        self.maybe_rename(os.path.join(root, name))

  def maybe_rename(self, name):
    name = name.decode('utf-8')
    dirname = os.path.dirname(name)
    basename = os.path.basename(name)
    renamed = self.clean_name(basename)
    if basename != renamed:
      renamed = os.path.join(dirname, renamed)
      print "rename: %s\n     -> %s" % (name, renamed)
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
  cleaner = FilenameCleaner(ccdict_path=my_dir)
  cleaner.recursive_clean(sys.argv[1])

if __name__ == "__main__":
  main()
