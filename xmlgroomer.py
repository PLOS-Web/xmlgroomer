#!/usr/bin/env python
# usage: xmlgroomer.py before.xml after.xml

import sys
import subprocess
import re
import lxml.etree as etree
import mimetypes

groomers = []

def fix_article_type(root):
    for typ in root.xpath("//article-categories//subj-group[@subj-group-type='heading']/subject"):
        if typ.text == 'Clinical Trial':
            print 'changing article type from Clinical Trial to Research Article'
            typ.text = 'Research Article'
    return root
groomers.append(fix_article_type)

def fix_article_title(root):
    for title in root.xpath("//title-group/article-title"):
        if re.search(r'[\t\n\r]', title.text):
            new_title = re.sub(r'[\t\n\r]+', r'', title.text)
            print 'changing article title from', title.text, 'to', new_title
            title.text = new_title
    return root
groomers.append(fix_article_title)

def fix_pubdate(root):
    doi = root.xpath("//article-id[@pub-id-type='doi']")[0].text
    pubdate = subprocess.check_output(['php', '/var/local/scripts/production/getPubdate.php', doi])
    em = {'year':pubdate[:4], 'month':str(int(pubdate[5:7])), 'day':str(int(pubdate[8:]))}
    for date in root.xpath("//pub-date[@pub-type='epub']"):
        for field in ['year','month','day']:
            xml_val = date.xpath(field)[0].text
            if xml_val != em[field]:
                print 'changing pub', field, 'from', xml_val, 'to', em[field]
                date.xpath(field)[0].text = em[field]
    return root
groomers.append(fix_pubdate)

def fix_collection(root):
    for coll in root.xpath("//pub-date[@pub-type='collection']"):
        for field in ['year','month']:
            if coll.xpath(field):
                pub_val = root.xpath("//pub-date[@pub-type='epub']/"+field)[0].text
                xml_val = coll.xpath(field)[0].text
                if xml_val != pub_val:
                    print 'changing collection', field, 'from', xml_val, 'to', pub_val
                    coll.xpath(field)[0].text = pub_val
    return root
groomers.append(fix_collection)

def fix_volume(root):
    year = root.xpath("//pub-date[@pub-type='epub']/year")[0].text
    journal = root.xpath("//journal-id[@journal-id-type='pmc']")[0].text
    volumes = {'plosbiol':2002, 'plosmed':2003, 'ploscomp':2004, 'plosgen':2004, 'plospath':2004,
                'plosone':2005, 'plosntds':2006}
    for volume in root.xpath("//article-meta/volume"):
        correct_volume = str(int(year) - volumes[journal])
        if volume.text != correct_volume:
            print 'changing volume from', volume.text, 'to', correct_volume
            volume.text = correct_volume
    return root
groomers.append(fix_volume)

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

def fix_elocation(root):
    doi = root.xpath("//article-id[@pub-id-type='doi']")[0].text
    correct_eloc = 'e'+str(int(doi[-7:]))
    for eloc in root.xpath("//elocation-id"):
        if eloc.text != correct_eloc:
            print 'changing elocation from', eloc.text, 'to', correct_eloc
            eloc.text = correct_eloc
    return root
groomers.append(fix_elocation)

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

def fix_mimetype(root):
    for sup in root.xpath("//supplementary-material"):
        typ = sup.xpath("caption/p")[-1].text.strip('()')
        mime, enc = mimetypes.guess_type('x.'+typ, False)
        if not mime:
            print 'could not find mimetype'
            continue
        if 'mimetype' not in sup.attrib or mime != sup.attrib['mimetype']:
            print 'setting mimetype of', typ, 'to', mime
            sup.attrib['mimetype'] = mime
    return root
groomers.append(fix_mimetype)

def fix_empty_element(root):
    # starts from the leaves of the tree to remove nested empty elements
    for element in reversed(list(root.iterdescendants())):
        if not element.text and not element.attrib and not element.getchildren():
            print 'removing empty element', element.tag
            element.getparent().remove(element)
    return root
groomers.append(fix_empty_element)

if __name__ == '__main__':
    print "start grooming..."
    if len(sys.argv) != 3:
        sys.exit('usage: xmlgroomer.py before.xml after.xml')
    parser = etree.XMLParser(recover = True)
    e = etree.parse(sys.argv[1],parser)
    root = e.getroot()
    for groomer in groomers:
        root = groomer(root)
    e.write(sys.argv[2], xml_declaration = True, encoding = 'UTF-8')
    print 'grooming done'
