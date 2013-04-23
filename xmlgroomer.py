#!/usr/bin/env python
# usage: xmlgroomer.py before.xml after.xml

import sys
import re
import lxml.etree as etree

groomers = []

def fix_article_type(root):
    for article_type in root.xpath("//article-categories//subj-group[@subj-group-type='heading']/subject"):
        if article_type.text == 'Clinical Trial':
            print 'changing article type from Clinical Trial to Research Article'
            article_type.text = 'Research Article'
    return root
groomers.append(fix_article_type)

def fix_pubdate(root, pubdate):
    em = {'year':pubdate[:4], 'month':str(int(pubdate[5:7])), 'day':str(int(pubdate[8:]))}
    for date in root.xpath("//pub-date[@pub-type='epub']"):
        for field in ['year','month','day']:
            xml_val = date.xpath(field)[0].text
            if xml_val != em[field]:
                print 'changing pub', field, 'from', xml_val, 'to', em[field]
                date.xpath(field)[0].text = em[field]
    return root
# groomers.append(fix_pubdate)

def fix_collection(root):
    pub = {}
    pub['year'] = root.xpath("//pub-date[@pub-type='epub']/year")[0].text
    pub['month'] = root.xpath("//pub-date[@pub-type='epub']/month")[0].text
    for coll in root.xpath("//pub-date[@pub-type='collection']"):
        for field in ['year','month']:
            if coll.xpath(field):
                xml_val = coll.xpath(field)[0].text
                if xml_val != pub[field]:
                    print 'changing collection', field, 'from', xml_val, 'to', pub[field]
                    coll.xpath(field)[0].text = pub[field]
    return root
groomers.append(fix_collection)

def fix_issue(root):
    month = root.xpath("//pub-date[@pub-type='epub']/month")[0].text
    for issue in root.xpath("//article-meta/issue"):
        if issue.text != month:
            print 'changing issue from', issue.text, 'to', month
            issue.text = month
    return root
groomers.append(fix_issue)

def fix_copyright(root):
    year = root.xpath("//pub-date[@pub-type='epub']/year")[0].text
    for copyright in root.xpath("//article-meta//copyright-year"):
        if copyright.text != year:
            print 'changing copyright year from', copyright.text, 'to', year
            copyright.text = year
    return root
groomers.append(fix_copyright)

def fix_journal_ref(root):
    for link in root.xpath("//mixed-citation[@publication-type='journal']/ext-link"):
        print 'adding comment tag around journal reference link'
        parent = link.getparent()
        index = parent.index(link)
        comment = etree.Element('comment')
        comment.append(link)
        previous = parent.getchildren()[index-1]
        if previous.tail:
            comment.text = previous.tail
            previous.tail = ''
        parent.insert(index, comment)
    return root
groomers.append(fix_journal_ref)

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
groomers.append(fix_url)

def fix_comment(root):
    for comment in root.xpath("//comment"):
        if comment.tail:
            print 'removing period after comment end tag'
            comment.tail = re.sub(r'^\.', r'', comment.tail)
    return root
groomers.append(fix_comment)

def fix_provenance(root):
    for prov in root.xpath("//author-notes//fn[@fn-type='other']"):
        if prov.xpath("p/bold")[0].text == 'Provenance:':
            print 'moving provenance from author-notes to fn-group after references'
            fngroup = etree.Element('fn-group')
            fngroup.append(prov)
            reflist = root.xpath("//ref-list")[0]
            parent = reflist.getparent()
            parent.insert(parent.index(reflist) + 1, fngroup)
    return root
groomers.append(fix_provenance)

def fix_empty_element(root):
    for element in root.iterdescendants():
        if not element.text and not element.attrib and not element.getchildren():
            print 'removing empty element', element.tag
            element.getparent().remove(element)        
    return root
groomers.append(fix_empty_element)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: xmlgroomer.py before.xml after.xml')
    parser = etree.XMLParser(recover=True)
    e = etree.parse(sys.argv[1],parser)
    root = e.getroot()
    for groomer in groomers:
        root = groomer(root)
    e.write(sys.argv[2], xml_declaration = True, encoding = 'UTF-8')
    print 'done'
