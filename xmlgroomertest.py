#!/usr/bin/env python
# usage: nosetests xmlgroomertest.py

import sys
import re
import lxml.etree as etree
import xmlgroomer as x

def test_fix_url():
    before = etree.fromstring(\
        '<article xmlns:xlink="http://www.w3.org/1999/xlink">\
        <ext-link ext-link-type="uri" xlink:href="ht tp://10.1023/A:1020  830703012" xlink:type="simple">\
        </ext-link>\
        </article>')
    after = etree.fromstring(\
        '<article xmlns:xlink="http://www.w3.org/1999/xlink">\
        <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1023/A:1020830703012" xlink:type="simple">\
        </ext-link>\
        </article>')
    assert etree.tostring(after) == etree.tostring(x.fix_url(before))

def test_change_Clinical_Trial_to_Research_Article():
    before = etree.fromstring(\
        '<article>\
        <article-categories>\
        <subj-group subj-group-type="heading">\
        <subject>Clinical Trial</subject>\
        </subj-group>\
        </article-categories>\
        </article>')
    after = etree.fromstring(\
        '<article>\
        <article-categories>\
        <subj-group subj-group-type="heading">\
        <subject>Research Article</subject>\
        </subj-group>\
        </article-categories>\
        </article>')
    assert etree.tostring(after) == etree.tostring(x.change_Clinical_Trial_to_Research_Article(before))

def test_remove_period_after_comment_end_tag():
    before = etree.fromstring('<article><comment></comment>.</article>')
    after = etree.fromstring('<article><comment></comment></article>')
    assert etree.tostring(after) == etree.tostring(x.remove_period_after_comment_end_tag(before))
