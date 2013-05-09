#!/usr/bin/env python
# usage: xmlgroomer.py before.xml after.xml

import sys
import subprocess
import lxml.etree as etree
import mimetypes
import re

groomers = []
output = ''

def fix_article_type(root):
    global output
    for typ in root.xpath("//article-categories//subj-group[@subj-group-type='heading']/subject"):
        if typ.text == 'Clinical Trial':
            output += 'correction: changed article type from Clinical Trial to Research Article\n'
            typ.text = 'Research Article'
    return root
groomers.append(fix_article_type)

def fix_article_title(root):
    global output
    for title in root.xpath("//title-group/article-title"):
        if re.search(r'[\t\n\r]| {2,}', unicode(title.text)):
            new_title = re.sub(r'[\t\n\r ]+', r' ', unicode(title.text))
            output += 'correction: changed article title from '+title.text+' to '+new_title+'\n'
            title.text = new_title
    return root
groomers.append(fix_article_title)

def fix_pubdate(root):
    global output
    doi = root.xpath("//article-id[@pub-id-type='doi']")[0].text
    proc = subprocess.Popen(['php', '/var/local/scripts/production/getPubdate.php', doi], shell=False, stdout=subprocess.PIPE)
    pubdate = proc.communicate()[0]
    em = {'year':pubdate[:4], 'month':str(int(pubdate[5:7])), 'day':str(int(pubdate[8:]))}
    for date in root.xpath("//pub-date[@pub-type='epub']"):
        for field in ['year','month','day']:
            xml_val = date.xpath(field)[0].text
            if xml_val != em[field]:
                output += 'correction: changed pub '+field+' from '+xml_val+' to '+em[field]+'\n'
                date.xpath(field)[0].text = em[field]
    return root
groomers.append(fix_pubdate)

def fix_collection(root):
    global output
    for coll in root.xpath("//pub-date[@pub-type='collection']"):
        for field in ['year','month']:
            if coll.xpath(field):
                pub_val = root.xpath("//pub-date[@pub-type='epub']/"+field)[0].text
                xml_val = coll.xpath(field)[0].text
                if xml_val != pub_val:
                    output += 'correction: changed collection '+field+' from '+xml_val+' to '+pub_val+'\n'
                    coll.xpath(field)[0].text = pub_val
    return root
groomers.append(fix_collection)

def fix_volume(root):
    global output
    year = root.xpath("//pub-date[@pub-type='epub']/year")[0].text
    journal = root.xpath("//journal-id[@journal-id-type='pmc']")[0].text
    volumes = {'plosbiol':2002, 'plosmed':2003, 'ploscomp':2004, 'plosgen':2004, 'plospath':2004,
                'plosone':2005, 'plosntds':2006}
    for volume in root.xpath("//article-meta/volume"):
        correct_volume = str(int(year) - volumes[journal])
        if volume.text != correct_volume:
            output += 'correction: changed volume from '+volume.text+' to '+correct_volume+'\n'
            volume.text = correct_volume
    return root
groomers.append(fix_volume)

def fix_issue(root):
    global output
    month = root.xpath("//pub-date[@pub-type='epub']/month")[0].text
    for issue in root.xpath("//article-meta/issue"):
        if issue.text != month:
            output += 'correction: changed issue from '+issue.text+' to '+month+'\n'
            issue.text = month
    return root
groomers.append(fix_issue)

def fix_copyright(root):
    global output
    year = root.xpath("//pub-date[@pub-type='epub']/year")[0].text
    for copyright in root.xpath("//article-meta//copyright-year"):
        if copyright.text != year:
            output += 'correction: changed copyright year from '+copyright.text+' to '+year+'\n'
            copyright.text = year
    return root
groomers.append(fix_copyright)

def fix_elocation(root):
    global output
    doi = root.xpath("//article-id[@pub-id-type='doi']")[0].text
    correct_eloc = 'e'+str(int(doi[-7:]))
    elocs = root.xpath("//elocation-id")
    for eloc in elocs:
        if eloc.text != correct_eloc:
            output += 'correction: changed elocation from '+eloc.text+' to '+correct_eloc+'\n'
            eloc.text = correct_eloc
    if not elocs:
        eloc = etree.Element('elocation-id')
        eloc.text = correct_eloc
        issue = root.xpath("//article-meta/issue")[0]
        parent = issue.getparent()
        output += 'correction: added missing elocation '+correct_eloc+'\n'
        parent.insert(parent.index(issue) + 1, eloc)  
    return root
groomers.append(fix_elocation)

def fix_journal_ref(root):
    global output
    for link in root.xpath("//mixed-citation[@publication-type='journal']/ext-link"):
        parent = link.getparent()
        refnum = parent.getparent().xpath("label")[0].text
        index = parent.index(link)
        comment = etree.Element('comment')
        comment.append(link)
        previous = parent.getchildren()[index-1]
        if previous.tail:
            comment.text = previous.tail
            previous.tail = ''
        output += 'correction: added comment tag around journal reference '+refnum+' link\n'
        parent.insert(index, comment)
    return root
groomers.append(fix_journal_ref)

def fix_url(root):
    global output
    for link in root.xpath("//ext-link"):
        h = '{http://www.w3.org/1999/xlink}href'
        assert h in link.attrib  # error: ext-link does not have href
        # remove whitespace
        if re.search(r'\s', link.attrib[h]):
            new_link = re.sub(r'\s', r'', link.attrib[h])
            output += 'correction: changed link from '+link.attrib[h]+' to '+new_link+'\n'
            link.attrib[h] = new_link
        # prepend dx.doi.org if url is only a doi
        if re.match(r'http://10.[0-9]{4}', link.attrib[h]):
            new_link = link.attrib[h].replace('http://', 'http://dx.doi.org/')
            output += 'correction: changed link from '+link.attrib[h]+' to '+new_link+'\n'
            link.attrib[h] = new_link
    return root
groomers.append(fix_url)

def fix_comment(root):
    global output
    for comment in root.xpath("//comment"):
        if comment.tail:
            refnum = comment.getparent().getparent().xpath("label")[0].text
            output += 'correction: removed period after comment end tag in journal reference '+refnum+'\n'
            comment.tail = re.sub(r'^\.', r'', comment.tail)
    return root
groomers.append(fix_comment)

def fix_provenance(root):
    global output
    for prov in root.xpath("//author-notes//fn[@fn-type='other']/p/bold"):
        if prov.text == 'Provenance:':
            fngroup = etree.Element('fn-group')
            fngroup.append(prov.getparent().getparent())
            reflist = root.xpath("//ref-list")[0]
            parent = reflist.getparent()
            output += 'correction: moved provenance from author-notes to fn-group after references\n'
            parent.insert(parent.index(reflist) + 1, fngroup)
    return root
groomers.append(fix_provenance)

def fix_mimetype(root):
    global output
    for sup in root.xpath("//supplementary-material"):
        typ = sup.xpath("caption/p")[-1].text.strip('()')
        mime, enc = mimetypes.guess_type('x.'+typ, False)
        if 'mimetype' not in sup.attrib or mime != sup.attrib['mimetype']:
            output += 'correction: set mimetype of '+typ+' to '+mime+' for '+sup.xpath("label")[0].text+'\n'
            sup.attrib['mimetype'] = mime
    return root
groomers.append(fix_mimetype)

def fix_empty_element(root):
    global output
    # starts from the leaves of the tree to remove nested empty elements
    for element in reversed(list(root.iterdescendants())):
        if not element.text and not element.attrib and not element.getchildren():
            output += 'correction: removed empty element '+element.tag+' at '+root.getroottree().getpath(element)+'\n'
            element.getparent().remove(element)
    return root
groomers.append(fix_empty_element)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: xmlgroomer.py before.xml after.xml')
    print 'start grooming...'
    parser = etree.XMLParser(recover = True)
    e = etree.parse(sys.argv[1],parser)
    root = e.getroot()
    for groomer in groomers:
        root = groomer(root)
    e.write(sys.argv[2], xml_declaration = True, encoding = 'UTF-8')
    print output, 'grooming done'
