# -*- coding: utf-8 -*-
# Copyright: Ankitects Pty Ltd and contributors
# Used/unused kanji list code originally by 'LaC'
# Modification Mezase
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

import unicodedata
from anki.utils import ids2str, splitFields
from aqt.webview import AnkiWebView
from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom
from .notetypes import isJapaneseNoteType
from aqt import mw
config = mw.addonManager.getConfig(__name__)

# Backwards compatibility
try:
    UNICODE_EXISTS = bool(type(unicode)) # Python 2.X
except NameError:
    unicode = lambda *s: str(s) # Python 3+
try:
    range = xrange # Python 2.X
except NameError:
    pass # Python 3+

def isKanji(unichar):
    try:
        return unicodedata.name(unichar).find('CJK UNIFIED IDEOGRAPH') >= 0
    except ValueError:
        # a control character
        return False

class KanjiStats(object):

    def __init__(self, kanjiGrades,col, wholeCollection):
        self.col = col
        if wholeCollection:
            self.lim = ""
        else:
            self.lim = " and c.did in %s" % ids2str(self.col.decks.active())
        self._gradeHash = dict()
        for (name, chars), grade in zip(kanjiGrades,
                                        range(len(kanjiGrades))):
            for c in chars:
                self._gradeHash[c] = grade

    def kanjiGrade(self, unichar):
        return self._gradeHash.get(unichar, 0)

    # FIXME: as it's html, the width doesn't matter
    def kanjiCountStr(self, gradename, count, total=0, width=0):
        d = {'count': self.rjustfig(count, width), 'gradename': gradename}
        if total:
            d['total'] = self.rjustfig(total, width)
            d['percent'] = float(count)/total*100
            return ("%(gradename)s: %(count)s of %(total)s (%(percent)0.1f%%).") % d
        else:
            return ("%(count)s %(gradename)s kanji.") % d

    def rjustfig(self, n, width):
        n = unicode(n)
        return n + "&nbsp;" * (width - len(n))

    def genKanjiSets(self,kanjiGrades):
        self.kanjiSets = [set([]) for g in kanjiGrades]
        chars = set()
        for m in self.col.models.all():
            _noteName = m['name'].lower()
            if not isJapaneseNoteType(_noteName):
                continue

            idxs = []
            for c, name in enumerate(self.col.models.fieldNames(m)):
                for f in config['srcFields']:
                    if f.lower() in name.lower():
                        idxs.append(c)
            for row in self.col.db.execute("""
select flds from notes where id in (
select n.id from cards c, notes n
where c.nid = n.id and mid = ? and c.queue > 0
%s) """ % self.lim, m['id']):
                flds = splitFields(row[0])
                for idx in idxs:
                    chars.update(flds[idx])
        for c in chars:
            if isKanji(c):
                self.kanjiSets[self.kanjiGrade(c)].add(c)

    def report(self,kanjiGrades):
        self.genKanjiSets(kanjiGrades)
        counts = [(name, len(found), len(all)) \
                  for (name, all), found in zip(kanjiGrades, self.kanjiSets)]
        out = ((("<h1>Kanji statistics</h1>The seen cards in this %s "
                 "contain:") % (self.lim and "deck" or "collection")) +
               "<ul>" +
               # total kanji unique
               ("<li>%d total unique kanji.</li>") %
               sum([c[1] for c in counts]))
        count = sum([c[1] for c in counts])
        d = {'count': self.rjustfig(count, 3)}
        total = sum([c[2] for c in counts])
        d['total'] = self.rjustfig(total,3)
        d['percent'] = float(count/total*100)
        out += ("<li>Total : %(count)s of %(total)s (%(percent)0.1f%%).</li>") % d
		#Most Used
        out += "</ul><p/>" + (u"Most Used :") + "<p/><ul>"
        L = ["<li>" + self.kanjiCountStr(c[0],c[1],c[2], width=3) + "</li>"
			for c in counts[1:26]]
        out += "".join(L)
        out += "</ul>"
        return out

    def missingReport(self,kanjiGrades, check=None):
        if not check:
            check = lambda x, y: x not in y
            out = ("<h1>Missing</h1>")
        else:
            out = ("<h1>Seen</h1>")
        for grade in range(1, len(kanjiGrades)):
            missing = "".join(self.missingInGrade(kanjiGrades,grade, check))
            if not missing:
                continue
            out += "<h2>" + kanjiGrades[grade][0] + "</h2>"
            out += "<font size=+2>"
            out += self.mkEdict(missing)
            out += "</font>"
        return out + "<br/>"

    def mkEdict(self, kanji):
        out = "<font size=+2>"
        while 1:
            if not kanji:
                out += "</font>"
                return out
            # edict will take up to about 10 kanji at once
            out += self.edictKanjiLink(kanji[0:10])
            kanji = kanji[10:]

    def seenReport(self,kanjiGrades):
        return self.missingReport(kanjiGrades,lambda x, y: x in y)

    def nonJouyouReport(self):
        out = ("<h1>Non-Jouyou</h1>")
        out += self.mkEdict("".join(self.kanjiSets[0]))
        return out + "<br/>"

    def edictKanjiLink(self, kanji):
        base="http://nihongo.monash.edu/cgi-bin/wwwjdic?1MMJ"
        url=base + kanji
        return '<a href="%s">%s</a>' % (url, kanji)

    def missingInGrade(self, kanjiGrades,gradeNum, check):
        existingKanji = self.kanjiSets[gradeNum]
        totalKanji = kanjiGrades[gradeNum][1]
        return [k for k in totalKanji if check(k, existingKanji)]

def genKanjiStats(kanjiGrades):
    wholeCollection = mw.state == "deckBrowser"
    s = KanjiStats(kanjiGrades,mw.col, wholeCollection)
    rep = s.report(kanjiGrades)
    rep += s.seenReport(kanjiGrades)
    rep += s.missingReport(kanjiGrades)
    rep += s.nonJouyouReport()
    return rep