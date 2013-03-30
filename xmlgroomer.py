#!/usr/bin/env python
# usage: xmlgroomer.py before.xml after.xml

import sys
import re
import lxml.etree as etree

def fix_url(root):
    for link in root.xpath("//ext-link"):
        h = '{http://www.w3.org/1999/xlink}href'
        assert h in link.attrib  # error: ext-link does not have href
        # remove whitespace
        if re.search(r'\s', link.attrib[h]):
            new_link = re.sub(r'\s', r'', link.attrib[h])
            print 'changing link from', link.attrib[h], 'to', new_link
            link.attrib[h] = new_link
        # prepend dx.doi.org if url is only a doi
        if re.match(r'http://10.[0-9]{4}', link.attrib[h]):
            new_link = link.attrib[h].replace('http://', 'http://dx.doi.org/')
            print 'changing link from', link.attrib[h], 'to', new_link
            link.attrib[h] = new_link
    return root

def change_Clinical_Trial_to_Research_Article(root):
    for article_type in root.xpath("//article-categories//subj-group[@subj-group-type='heading']/subject"):
        if article_type.text == 'Clinical Trial':
            print 'changing article type from Clinical Trial to Research Article'
            article_type.text = 'Research Article'
    return root

def remove_period_after_comment_end_tag(root):
    for comment in root.xpath("//comment"):
        if comment.tail:
            print 'removing period after comment end tag'
            comment.tail = re.sub(r'^\.', r'', comment.tail)
    return root

if __name__ == '__main__':
    if len(sys.argv) == 3:
        e = etree.parse(sys.argv[1])
        root = e.getroot()
        fix_url(root)
        change_Clinical_Trial_to_Research_Article(root)
        remove_period_after_comment_end_tag(root)
        e.write(sys.argv[2], xml_declaration = True, encoding = 'UTF-8')
        print 'done'
    else:
        print 'usage: xmlgroomer.py before.xml after.xml'
