#!/usr/bin/env python
# usage: nosetests xmlgroomertest.py

import sys
import re
import lxml.etree as etree
import xmlgroomer as x

def verify(before, after, groomer):
    goal = normalize(after)
    result = normalize(etree.tostring(groomer(etree.fromstring(before))))
    if goal != result:
        print 'goal:\n', goal
        print 'result:\n', result
        assert False

def normalize(string):
    string = ''.join([line.strip() for line in string.split('\n')])
    return etree.tostring(etree.fromstring(string))

def test_fix_url():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <ext-link ext-link-type="uri" xlink:href="ht tp://10.1023/A:1020  830703012" xlink:type="simple">
        </ext-link>
        </article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1023/A:1020830703012" xlink:type="simple">
        </ext-link>
        </article>'''
    verify(before, after, x.fix_url)

def test_change_Clinical_Trial_to_Research_Article():
    before = '''<article>
        <article-categories>
        <subj-group subj-group-type="heading">
        <subject>Clinical Trial</subject>
        </subj-group>
        </article-categories>
        </article>'''
    after = '''<article>
        <article-categories>
        <subj-group subj-group-type="heading">
        <subject>Research Article</subject>
        </subj-group>
        </article-categories>
        </article>'''
    verify(before, after, x.change_Clinical_Trial_to_Research_Article)

def test_remove_period_after_comment_end_tag():
    before = '<article><comment></comment>.</article>'
    after = '<article><comment></comment></article>'
    verify(before, after, x.remove_period_after_comment_end_tag)

def test_move_provenance():
    before = '''<article>
        <author-notes>
        <fn fn-type="other">
        <p><bold>Provenance:</bold> Not commissioned; externally peer reviewed.</p>
        </fn>
        </author-notes>
        <ref-list></ref-list>
        <glossary></glossary>
        </article>'''
    after = '''<article>
        <author-notes></author-notes>
        <ref-list></ref-list>
        <fn-group>
        <fn fn-type="other">
        <p><bold>Provenance:</bold> Not commissioned; externally peer reviewed.</p>
        </fn>
        </fn-group>
        <glossary></glossary>
        </article>'''
    verify(before, after, x.move_provenance)

def test_remove_empty_element():
    before = '<article><tag><title></title></tag><sec id="s1"></sec><p>Paragraph.</p><body/></article>'
    after = '<article><tag/><sec id="s1"></sec><p>Paragraph.</p></article>'
    verify(before, after, x.remove_empty_element)

def test_add_comment_tag_to_journal_ref():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <mixed-citation publication-type="journal" xlink:type="simple">
        <lpage>516</lpage>doi:
        <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1038/nature03236" xlink:type="simple">
        10.1038/nature03236</ext-link>
        </mixed-citation> 
        </article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <mixed-citation publication-type="journal" xlink:type="simple">
        <lpage>516</lpage>
        <comment>doi:
        <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1038/nature03236" xlink:type="simple">
        10.1038/nature03236</ext-link>
        </comment>
        </mixed-citation> 
        </article>'''
    verify(before, after, x.add_comment_tag_to_journal_ref)
