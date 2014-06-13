#!/usr/bin/env python
# usage: xmlgroomer.py before.xml after.xml

import sys
import time
import subprocess
import lxml.etree as etree
from lxml import html
import mimetypes
import re
import traceback
import string
import argparse


groomers = []
validators = []
char_stream_groomers = []
output = ''


def register_groom(fn):
    global groomers
    groomers.append(fn)
    return fn


def register_validator(fn):
    global validators
    validators.append(fn)
    return fn


def register_char_stream_groom(fn):
    global groomers
    char_stream_groomers.append(fn)
    return fn


def get_doi(root):
    return root.xpath("//article-id[@pub-id-type='doi']")[0].text


def get_singular_node(elmnt, path):
    """Get an insured singular etree node via xpath
        Args:
        elmnt = etree object
        path = specific node within elmnt we're looking for
        Returns single node specified in path or raises and error
        if node doesn't exist or too many exist.
    """
    matches = elmnt.xpath(path)
    if len(matches) > 1:
        raise ValueError("Found %s %s(s) when only looking for 1" %
                         (len(elmnt.xpath(path)), path))
    elif len(matches) == 0:
        raise ValueError("%s doesn't exist!" % (path))
    else:
        return matches[0]


def fix_article_type(root):
    global output
    atitle = get_singular_node(root, "//article-categories//subj-group[@subj-group-type='heading']/subject")
    bad = ['Clinical Trial', 'Research article', 'Research Articles']
    if atitle.text in bad:
        old = atitle.text
        atitle.text = 'Research Article'
        output += 'correction: changed article type from "%s" to "Research Article"\n' % old
    return root
groomers.append(fix_article_type)


def check_correction_article(root):
    global output
    cxns = ['Correction', 'Retraction', 'Expression of Concern']
    if get_singular_node(root, "//article-categories//subj-group[@subj-group-type='heading']/subject").text in cxns:
        try:
            subj = get_singular_node(root, "//article-categories//subj-group[@subj-group-type='heading']/subject").text
            ra = get_singular_node(root,'//article-meta/related-article')
            article = get_singular_node(root, '//article')
            if subj == 'Correction' and ra.attrib['related-article-type'] != 'corrected-article':
                output += "error: related-article-type is not 'corrected-article'\n"
            elif ra.attrib['related-article-type'] == 'corrected-article' and article.attrib['article-type'] != 'correction':
                output += "error: article element article-type attribute not 'correction'\n"
            elif subj == 'Retraction':
                if ra.attrib['related-article-type'] != 'retracted-article':
                    oldratype = ra.attrib['related-article-type']
                    ra.attrib['related-article-type'] = 'retracted-article'
                    output += "correction: related-article-type changed from "+oldratype+" to 'retracted-article'\n"
                if article.attrib['article-type'] != 'retraction':
                    oldaatype = article.attrib['article-type']
                    article.attrib['article-type'] = 'retraction'
                    output += "correction: article element article-type attribute changed from "+oldaatype+" to 'retraction'\n"
            elif subj == 'Expression of Concern' and ra.attrib['related-article-type'] != 'object-of-concern':
                output += "error: related-article-type is not 'object-of-concern'\n"
            elif ra.attrib['related-article-type'] == 'object-of-concern' and article.attrib['article-type'] != 'expression-of-concern':
                output += "error: article element article-type attribute not 'expression-of-concern'\n"
        except ValueError:
            output += 'error: no related article element\n'
    return root
groomers.append(check_correction_article)


def fix_subject_category(root):
    global output
    discipline_v2 = (root.xpath("//subj-group"
                                "[@subj-group-type='Discipline-v2']"))
    if discipline_v2:
        for subj in discipline_v2:
            subj.getparent().remove(subj)
        output += 'correction: removed Discipline-v2 categories\n'
    return root
#groomers.append(fix_subject_category)


def fix_article_title(root):
    global output
    for title in root.xpath("//title-group/article-title"):
        if re.search(r'[\t\n\r]| {2,}', unicode(title.text)):
            old_title = title.text
            title.text = re.sub(r'[\t\n\r ]+', r' ', unicode(title.text))
            output += 'correction: changed article title from '\
                      + old_title + ' to ' + title.text + '\n'
    return root
groomers.append(fix_article_title)


def fix_bad_italic_tags_running_title(root):
    global output
    changed = False
    for typ in (root.xpath("//title-group/alt-title"
                           "[@alt-title-type='running-head']")):
        if not typ.text:
            continue
        atitle = html.fromstring(typ.text)
        if atitle.xpath('//i'):
            for i in atitle.xpath('//i'):
                i.tag = 'italic'
            atitle.tag = 'alt-title'
            atitle.attrib['alt-title-type'] = 'running-head'
            typ.getparent().replace(typ, atitle)
            changed = True
    if changed:
        output += 'correction: fixed italic tags in running title\n'''
    return root
groomers.append(fix_bad_italic_tags_running_title)


def fix_affiliation(root):
    global output
    for author in root.xpath("//contrib[@contrib-type='author']"):
        aff = author.xpath("xref[@ref-type='aff']")
        name = (author.xpath("name/surname")[0].text
                if author.xpath("name/surname")
                else author.xpath("collab")[0].text)
        aff_count = len(root.xpath("//aff[starts-with(@id, 'aff')]"))
        if not aff:
            if aff_count == 1:
                author.insert(1, etree.fromstring("""<xref ref-type='aff' rid='aff1'/>"""))
                output += 'correction: set rid=aff1 for '+name+'\n'
        elif aff[0].attrib['rid'] == 'aff':
            aff[0].attrib['rid'] = 'aff1'
            output += 'correction: set rid=aff1 for '+name+'\n'
    return root
groomers.append(fix_affiliation)


def fix_addrline(root):
    global output
    for addrline in root.xpath("//aff/addr-line"):
        if addrline.tail in [',','.',':']:
            addrline.tail = ''
            output += 'correction: removed punctuation after addr-line in '\
                      + addrline.getparent().attrib['id'] + '\n'
    return root
groomers.append(fix_addrline)


def fix_corresp_email(root):
    global output
    for corresp in root.xpath("//corresp"):
        if not corresp.getchildren():
            email = re.sub(r'(\S+@\S+)', r'<email xlink:type="simple">\1</email>', corresp.text)
            temp = etree.fromstring('<temp xmlns:xlink="http://www.w3.org/1999/xlink">'
                                    + email + '</temp>')
            corresp.text = ''
            corresp.append(temp)
            etree.strip_tags(corresp, 'temp')
            output += 'correction: activated email in corresp '+corresp.attrib['id']+'\n'
    return root
groomers.append(fix_corresp_email)


def fix_pubdate(root):
    global output
    doi = get_doi(root)
    proc = subprocess.Popen(['php', '/var/local/scripts/production/getPubdate.php', doi], shell=False, stdout=subprocess.PIPE)
    pubdate = proc.communicate()[0]
    if int(pubdate[:4]) > 2000:
        em = {'year':pubdate[:4], 'month':str(int(pubdate[5:7])), 'day':str(int(pubdate[8:]))}
        for date in root.xpath("//pub-date[@pub-type='epub']"):
            for field in ['year','month','day']:
                xml_val = date.xpath(field)[0].text
                if xml_val != em[field]:
                    date.xpath(field)[0].text = em[field]
                    output += 'correction: changed pub '+field+' from '+xml_val+' to '+em[field]+'\n'
                    output += 'warning: Pub date has been changed, make sure PDF pub date info matches XML\n'
    return root
groomers.append(fix_pubdate)


@register_validator
def check_pubdate(root):
    global output

    #  Get EM Pubdate
    doi = get_doi(root)
    proc = subprocess.Popen(['php', '/var/local/scripts/production/getPubdate.php', doi], shell=False, stdout=subprocess.PIPE)
    pubdate = proc.communicate()[0]
    if not pubdate:
        output += "error: EM has no pubdate for this article\n"
        return root
    
    #  Get XML pubdate
    epubs = root.xpath("//pub-date[@pub-type='epub']")
    if len(epubs) < 1:  # error on missing pubdate
        output += "error: no epub date defined in xml\n"
        return root
    elif len(epubs) > 1:  # error on > 1 pubdate
        output += "error: more than one epub date defined in xml\n"
        return root

    #  Parse XML pubdate
    epub = epubs[0]
    epub_date = {}
    for field in ['year','month','day']:
        try:
            if field != 'year':
                epub_date[field] = epub.xpath('./' + field)[0].text.zfill(2)
            else:
                epub_date[field] = epub.xpath('./' + field)[0].text
        except IndexError, e:
            output +="error: missing field in xml epub date: %s\n" % field
            return root
        
    xml_pubdate_str = "%(year)s-%(month)s-%(day)s" % epub_date

    #  Check that EM and XML pubdate match
    if xml_pubdate_str != pubdate:
        output += ("error: pubdate defined in xml (%s) does not "
                   "match EM pubdate (%s)\n" %
                   (xml_pubdate_str,
                   pubdate))

    return root


def fix_pub_date_elements(root):
    '''
    Outer If statement in try: checks for 'collection' element. if
    it exists, it removes 'month' child if exists in ONE articles.
    Then it checks the year against epub's year.
    If 'collection' doesn't exist, the else: statement builds it and adds
    it in correct location.
    Last If statement checks for 'ppub' element, and removes it if it exists.
    '''
    global output
    year = get_singular_node(root, "//pub-date[@pub-type='epub']/year")
    month = get_singular_node(root, "//pub-date[@pub-type='epub']/month")
    if root.xpath("//pub-date[@pub-type='collection']"):
        for coll in root.xpath("//pub-date[@pub-type='collection']"):
            if get_singular_node(root, '//journal-title-group/journal-title').text == "PLoS ONE":
                if coll.xpath('month'):
                    mo = get_singular_node(coll, 'month')
                    mo.getparent().remove(mo)
                    output += 'correction: removed month from collection tag\n'
            else:
                pub_val = month.text
                xml_val = get_singular_node(coll, 'month').text
                if xml_val != pub_val:
                    get_singular_node(coll, 'month').text = pub_val
                    output += 'correction: changed collection month from '\
                              + xml_val + ' to ' + pub_val + '\n'

            if coll.xpath('year'):
                pub_val = year.text
                xml_val = get_singular_node(coll, 'year').text
                if xml_val != pub_val:
                    get_singular_node(coll, 'year').text = pub_val
                    output += 'correction: changed collection year from '\
                              + xml_val + ' to ' + pub_val + '\n'
    else:
        for pubds in root.xpath("//article-meta"):
            col = etree.Element('pub-date')
            col.attrib['pub-type'] = 'collection'
            aunotes = get_singular_node(root, "//article-meta/author-notes")
            parent = aunotes.getparent()
            parent.insert(parent.index(aunotes) + 1, col)
            etree.SubElement(col, 'year').text = year.text
            output += 'correction: added missing "collection" pub-type\n'
    if root.xpath("//pub-date[@pub-type='ppub']"):
        ppub = get_singular_node(root, "//pub-date[@pub-type='ppub']")
        ppub.getparent().remove(ppub)
        output+= 'correction: removed pub-date element with "ppub" type\n'
    return root
groomers.append(fix_pub_date_elements)


def fix_volume(root):
    global output
    year = root.xpath("//pub-date[@pub-type='epub']/year")[0].text
    journal = root.xpath("//journal-id[@journal-id-type='pmc']")[0].text
    volumes = {'plosbiol':2002, 'plosmed':2003, 'ploscomp':2004, 'plosgen':2004,
               'plospath':2004, 'plosone':2005, 'plosntds':2006}
    for volume in root.xpath("//article-meta/volume"):
        correct_volume = str(int(year) - volumes[journal])
        if volume.text != correct_volume:
            old_volume = volume.text
            volume.text = correct_volume
            output += 'correction: changed volume from '+old_volume+' to '+volume.text+'\n'
            output += 'warning: Volume has been changed, make sure PDF citation and footer info matches XML\n'
    return root
groomers.append(fix_volume)


def fix_issue(root):
    global output
    month = root.xpath("//pub-date[@pub-type='epub']/month")[0].text
    for issue in root.xpath("//article-meta/issue"):
        if issue.text != month:
            old_issue = issue.text
            issue.text = month
            output += 'correction: changed issue from '+old_issue+' to '+issue.text+'\n'
            output += 'warning: Issue has been changed, make sure PDF citation and footer info matches XML\n'
    return root
groomers.append(fix_issue)


def fix_copyright(root):
    global output
    year = root.xpath("//pub-date[@pub-type='epub']/year")[0].text
    for copyright in root.xpath("//article-meta//copyright-year"):
        if copyright.text != year:
            old_copyright = copyright.text
            copyright.text = year
            output += 'correction: changed copyright year from '\
                      + old_copyright + ' to ' + copyright.text + '\n'
    return root
groomers.append(fix_copyright)


def add_creative_commons_copyright_link(root):
    global output
    for statement in root.xpath("//permissions/license/license-p"):
        if len(statement.xpath("ext-link")) == 0:
            if statement.text[30:36] == " distr":
                l = etree.SubElement(statement, "ext-link")
                l.attrib['ext-link-type'] = 'uri'
                statement.text = 'This is an open-access article distributed under the terms of the '
                l.attrib['{http://www.w3.org/1999/xlink}href'] = 'http://creativecommons.org/licenses/by/4.0/'
                l.text = "Creative Commons Attribution License"
                l.tail = (', which permits unrestricted use, distribution, '
                          'and reproduction in any medium, provided the original '
                          'author and source are credited.')
                for attr in root.xpath("//permissions/license"):
                    attr.attrib['{http://www.w3.org/1999/xlink}href'] = 'http://creativecommons.org/licenses/by/4.0/'
            elif statement.text[30:36] == ", free":
                pass
            else:
                output += 'warning: License text was not recognized CC license, CC link not added\n'
    return root
groomers.append(add_creative_commons_copyright_link)


def fix_elocation(root):
    global output
    doi = get_doi(root)
    correct_eloc = 'e'+str(int(doi[-7:]))
    elocs = root.xpath("//elocation-id")
    for eloc in elocs:
        if eloc.text != correct_eloc:
            old_eloc = eloc.text
            eloc.text = correct_eloc
            output += 'correction: changed elocation from '+old_eloc+' to '+eloc.text+'\n'
    if not elocs:
        eloc = etree.Element('elocation-id')
        eloc.text = correct_eloc
        issue = root.xpath("//article-meta/issue")[0]
        parent = issue.getparent()
        parent.insert(parent.index(issue) + 1, eloc)
        output += 'correction: added missing elocation '+eloc.text+'\n'
    return root
groomers.append(fix_elocation)


def fix_fpage_lpage_in_meta(root):
    global output
    changed = False
    if root.xpath("//article-meta/fpage"):
        fp = get_singular_node(root, "//article-meta/fpage")
        fp.getparent().remove(fp)
        changed = True
    if root.xpath("//article-meta/lpage"):
        lp = get_singular_node(root, "//article-meta/lpage")
        lp.getparent().remove(lp)
        changed = True
    if changed:
        output += "correction: removed fpage/lpage tag(s) from article-meta\n"
    return root
groomers.append(fix_fpage_lpage_in_meta)


def fix_related_article(root):
    global output
    h = '{http://www.w3.org/1999/xlink}href'
    related = root.xpath("//related-article")
    for link in related:
        if re.match(r'info:doi/[a-z]{4}\.[0-9]{7}', link.attrib[h]):
            old_link = link.attrib[h]
            link.attrib[h] = link.attrib[h].replace('info:doi/', 'info:doi/10.1371/journal.')
            output += 'correction: changed related article link from '+old_link+' to '+link.attrib[h]+'\n'
    return root
groomers.append(fix_related_article)


def fix_title(root):
    global output
    for title in root.xpath("//title"):
        title_str = etree.tostring(title)
        if re.search(r'\s</title>', title_str):
            title.getparent().replace(title, etree.fromstring(re.sub(r'\s*</title>', r'</title>', title_str)))
            text = title.text if title.text else title.getchildren()[0].text+title.getchildren()[0].tail
            output += 'correction: removed whitespace from end of title '+text+'\n'
    return root
groomers.append(fix_title)


def fix_headed_title(root):
    global output
    for title in root.xpath("//sec[@sec-type='headed']/title"):
        if re.search(r':$', title.text):
            old_title = title.text
            title.text = re.sub(r':$', r'', title.text)
            output += 'correction: removed punctuation from headed title '+old_title+'\n'
    return root
groomers.append(fix_headed_title)


def fix_formula(root):
    global output
    for formula in root.xpath("//fig//caption//disp-formula") + root.xpath("//table//disp-formula"):
        formula.tag = 'inline-formula'
        formula.attrib.pop('id')
        graphic = formula.xpath("graphic")[0]
        graphic.tag = 'inline-graphic'
        graphic.attrib.pop('position')
        output += 'correction: changed disp-formula to inline-formula for '\
                  +graphic.attrib['{http://www.w3.org/1999/xlink}href']+'\n'
    return root
groomers.append(fix_formula)


def fix_formula_label(root):
    global output
    for label in root.xpath("//disp-formula/label"):
        old_label = label.text
        label.text = re.sub(r'[^0-9]*([0-9]\w*|[A-Z]).*', r'(\1)', label.text)
        if label.text != old_label:
            output += 'correction: changed disp-formula label from '+old_label+' to '+label.text+'\n'
    return root
#groomers.append(fix_formula_label)


def fix_label(root):
    global output
    refnums = ''
    for label in root.xpath("//ref/label"):
        for item in list(label.iterdescendants()):
            etree.strip_tags(label, item.tag)
            if label.text:
                refnums += label.text+' '
    if refnums:
        output += 'correction: removed tags inside reference labels '+refnums+'\n'
    return root
groomers.append(fix_label)


def fix_url(root):
    global output
    h = '{http://www.w3.org/1999/xlink}href'
    correction_count = 0
    for link in root.xpath("//ext-link"):
        old_link = link.attrib[h]
        # remove whitespace
        if re.search(r'\s', link.attrib[h]):
            link.attrib[h] = re.sub(r'\s', r'', link.attrib[h])
        # prepend http:// if not there
        if not link.attrib[h].startswith('http') and not link.attrib[h].startswith('ftp'):
            link.attrib[h] = 'http://' + link.attrib[h]
            output += 'correction: changed link from '+old_link+' to '+link.attrib[h]+'\n'
        # prepend dx.doi.org/ for doi
        if re.match(r'http://10\.[0-9]{4}', link.attrib[h]):
            link.attrib[h] = link.attrib[h].replace('http://', 'http://dx.doi.org/')
            correction_count += 1
        # prepend www.ncbi.nlm.nih.gov/pubmed/ for pmid
        if re.match(r'http://[0-9]{7,8}$', link.attrib[h]) or link.attrib['ext-link-type'] == 'pmid':
            link.attrib[h] = link.attrib[h].replace('http://', 'http://www.ncbi.nlm.nih.gov/pubmed/')
            correction_count += 1
    
    if correction_count > 0:
        output += "correction: fixed %i doi/pmid link(s).\n" % correction_count
    return root
groomers.append(fix_url)


def fix_page_range(root):
    global output
    for ref in root.xpath("//ref/mixed-citation"):
        fpages = ref.xpath("fpage")
        lpages = ref.xpath("lpage")
        refnum = ref.getparent().xpath("label")[0].text if len(fpages) > 1 or len(lpages) > 1 else ''
        if len(fpages) > 1:
            fpages[0].text = min([x.text for x in fpages + lpages])
            for page in fpages[1:]:
                ref.remove(page)
        if len(lpages) > 1:
            lpages[0].text = max([x.text for x in fpages + lpages])
            for page in lpages[1:]:
                ref.remove(page)
            lpages[0].tail = lpages[0].tail.replace(',','.')
        if refnum:
            output += 'correction: consolidated multiple fpage-lpage in reference '+refnum+'\n'
    return root
groomers.append(fix_page_range)


def fix_comment(root):
    global output
    refnums = ''
    for comment in root.xpath("//comment"):
        if comment.tail and comment.tail.startswith("."):
            comment.tail = re.sub(r'^\.', r'', comment.tail)
            refnums += list(comment.iterancestors("ref"))[0].xpath("label")[0].text+' '
    if refnums:
        output += 'correction: removed period after comment end tag in journal references '+refnums+'\n'
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
            parent.insert(parent.index(reflist) + 1, fngroup)
            output += 'correction: moved provenance from author-notes to fn-group after references\n'
    return root
groomers.append(fix_provenance)


def fix_remove_si_label_punctuation(root):
    global output
    changed = False
    for lab in root.xpath("//supplementary-material/label"):
        stripped = lab.text.strip(string.whitespace + string.punctuation)
        if lab.text != stripped:
            lab.text = stripped
            changed = True
    if changed:
        output += 'correction: removed punctuation from end of label tag text'
    return root
groomers.append(fix_remove_si_label_punctuation)


def fix_extension(root):
    global output
    for si in root.xpath("//supplementary-material"):
        typ = si.xpath("caption/p")[-1].text
        if re.match(r'^\(.*\)$', typ):
            filename = si.attrib['{http://www.w3.org/1999/xlink}href']
            ext = typ.strip('()').lower()
            if re.match(r's[0-9]{3}', filename[-4:]):
                si.attrib['{http://www.w3.org/1999/xlink}href'] = filename+'.'+ext
                output += 'correction: set extension of '\
                          +filename+' to '+ext+' for '+si.xpath("label")[0].text+'\n'
    return root
groomers.append(fix_extension)


def fix_mimetype(root):
    global output
    for si in root.xpath("//supplementary-material"):
        typ = si.xpath("caption/p")[-1].text
        if re.match(r'^\(.*\)$', typ):
            mime, enc = mimetypes.guess_type('x.'+typ.strip('()').lower(), False)
            if mime and ('mimetype' not in si.attrib or mime != si.attrib['mimetype']):
                si.attrib['mimetype'] = mime
                output += 'correction: set mimetype of '\
                          +typ+' to '+mime+' for '+si.xpath("label")[0].text+'\n'
    return root
groomers.append(fix_mimetype)


def remove_pua_set(char_stream):
    global output
    pua_set = ur'[\uE000-\uF8FF]'

    # form correction output
    display_width = 20
    for m in re.finditer(pua_set, char_stream):
        start = m.start() - display_width
        if (start < 0): start = 0
        end = m.start() + display_width
        if (end >= len(char_stream)): start = -1
        output += "correction: removed bad character at index=%s " \
                  "(marked by ^): \"%s^%s\"\n" \
                  % (m.start(), char_stream[start:m.start()], char_stream[m.start():end])

    # actually make the corrections
    char_stream = re.sub(pua_set, '', char_stream)

    return char_stream
char_stream_groomers.append(remove_pua_set)


@register_char_stream_groom
def alert_merops_validator_error(char_stream):
    global output
    merops_error_re = ur'\[!.{0,100}!\]'
    display_width = 20
    for m in re.finditer(merops_error_re, char_stream):
        start = m.start() - display_width
        if (start < 0): start = 0
        end = m.start() + display_width
        if (end >= len(char_stream)): start = -1
        output += ("error: located merops-inserted validation error, "
                   "please address and remove: \"%s%s\"\n" %
                   (char_stream[start:m.start()],
                    char_stream[m.start():end]))

    return char_stream


@register_groom
def check_article_type(root):
    global output
    article_types = ["Book Review","Book Review/Science in the Media","Community Page","Debate","Editorial",
                     "Education","Essay","Expert Commentary","Expression of Concern","Feature","From Innovation to Application",
                     "Guidelines and Guidance","Health in Action","Historical Profiles and Perspectives",
                     "Historical and Philosophical Perspectives","History/Profile","Interview","Journal Club","Learning Forum",
                     "Message from ISCB","Message from PLoS","Neglected Diseases","Obituary","Online Only: Editorial","Opinion",
                     "Overview","Perspective","Pearls","Photo Quiz","Policy Forum","Policy Platform","Primer","Reader Poll",
                     "Research Article","Research in Translation","Review","Special Report","Symposium","Synopsis",
                     "Technical Report","The PLoS Medicine Debate","Unsolved Mystery","Viewpoints", "Correction", "Retraction",
                     "Formal Comment"]
    for typ in root.xpath("//article-categories//subj-group[@subj-group-type='heading']/subject"):
        if typ.text not in article_types:
            output += 'error: '+typ.text+' is not a valid article type\n'
    return root


@register_groom
def check_misplaced_pullquotes(root):
    global output
    pull_quote_placed_last = root.xpath('//body/sec/p[last()]/named-content[@content-type="pullquote"]')
    if (pull_quote_placed_last):
        output += 'warning: pullquote appears as last element of a section\n'
    return root


@register_groom
def check_missing_blurb(root):
    global output
    journal = root.xpath("//journal-id[@journal-id-type='pmc']")[0].text

    blurb_journals = ['plosmed', 'plosbio']
    if journal in blurb_journals:
        abstract_toc = root.xpath('//article/front/article-meta/abstract[@abstract-type="toc"]')
        if not abstract_toc:
            output += "warning: article xml is missing 'blurb'\n"
    return root


@register_groom
def check_SI_attributes(root):
    global output

    doi = get_doi(root).split('10.1371/journal.')[1]

    for si in root.xpath("//article/body/sec/supplementary-material"):
        mimetype = si.get("mimetype")
        label = si.find("label")
        si_id = si.get("id")
        href = si.attrib['{http://www.w3.org/1999/xlink}href']
        #TODO: was href hash built here.  Need replacement

        if not mimetype:
            output += "error: mimetype missing: %s!\n" % si_id

        good_href_pattern = re.compile(r'%s\.[a-z0-9]+' % si_id)
        if not good_href_pattern.match(href):
            output += "error: bad or missing file extension: %s\n" % href

        doi_pattern = re.compile(r'%s' % doi)
        if not doi_pattern.match(href) or not doi_pattern.match(si_id):
            output += "error: supp info %s does not match doi: %s\n" % (href, doi)

    return root


@register_groom
def check_lowercase_extensions(root):
    global output

    for graphic in root.findall('graphic'):
        href = graphic.attrib['{http://www.w3.org/1999/xlink}href']
        if not re.match(r'.+?\.[gte][0-9]{3,4}\.[a-z0-9]+', href):
            output += "error: bad or missing file extension: %s\n" % href

    return root


@register_groom
def check_collab_markup(root):
    global output

    suspicious_pattern = "\S*\s\S*\s\S*\s\S*|\sthe\s|\sfor\s|\sof\s|\son\s|\sin\s|\swith\s|\sgroup\s|\scenter|\sorganization|\sorganizing|\scollaboration|\scollaborative\s|\scommittee|\scouncil|\sconsortium|\sassociation|\spartnership|\sproject|\steam|\ssociety\s"

    authors_names = root.xpath('//contrib[@contrib-type="author"]/name/surname | //contrib[@contrib-type="author"]/name/given-name')
    for name in authors_names:
        if re.search(suspicious_pattern, name.text, re.IGNORECASE):
            output += "warning: Article may contain incorrect markup for a " \
                      "collaborative author. Suspicious text to search for: " \
                      "%s\n" % name.text

    return root


#@register_groom
def check_on_behalf_of_markup(root):
    global output

    suspicious_words = ['for', 'on behalf of']
    for collab in root.xpath('//contrib-group/contrib/collab'):
        for word in suspicious_words:
            if re.match(word, collab.text, re.IGNORECASE):
                output += "warning: <collab> tag with value: %s.  " \
                          "There may be a missing <on-behalf-of>.\n" % collab.text
                break

    return root


@register_groom
def check_sec_ack_title(root):
    global output

    for fake_ack in root.xpath('//sec/title[text()="Acknowledgements"]'):
        output += "warning: there is a <sec> titled \'Acknowledgements\' " \
                  "rather than the use of an <ack> tag.\n"

    return root


@register_groom
def check_improper_children_in_funding_statement(root):
    global output

    invalid_tags = ['inline-formula', 'inline-graphic']
    for funding_statement in root.xpath('//funding-statement'):
        for elem in funding_statement:
            if elem.tag in invalid_tags:
                output += "error: funding-statement has illegal child node: %s\n" % elem.tag

    return root


@register_groom
def check_nlm_ta(root):
    global output
    nlm_tas = ["PLoS Biol", "PLoS Comput Biol", "PLoS Clin Trials",
               "PLoS Genet", "PLoS Med", "PLoS Negl Trop Dis", "PLoS One",
               "PLoS ONE", "PLoS Pathog", "PLoS Curr"]
    nlm_ta = root.xpath("//journal-meta/journal-id[@journal-id-type='nlm-ta']")
    if not nlm_ta:
        output += 'error: missing nlm-ta in metadata\n'
    elif nlm_ta[0].text not in nlm_tas:
        output += 'error: invalid nlm-ta in metadata: '+nlm_ta[0].text+'\n'
    return root
groomers.append(check_nlm_ta)


@register_groom
def check_valid_journal_title(root):
    global output

    valid_journal_titles = ["PLoS Biology", "PLoS Computational Biology",
                            "PLoS Clinical Trials", "PLoS Genetics",
                            "PLoS Medicine", "PLoS Neglected Tropical Diseases",
                            "PLoS ONE", "PLoS Pathogens", "PLoS Currents"]
    journal_title = root.xpath('/article/front/journal-meta/journal-title-group/journal-title')

    if not journal_title:
        output += "error: missing journal title in metadata\n"
    elif journal_title[0].text not in valid_journal_titles:
        output += "error: invalid journal title in metadata: %s\n" % journal_title[0].text

    return root


if __name__ == '__main__':
    parser = argparse.ArgumentParser("xmlgroomer.py before.xml after.xml\ndry run: xmlgroomer.py before.xml")
    parser.add_argument("-e", "--error-check", action='store_true')
    parser.add_argument("beforexml")
    parser.add_argument("afterxml", nargs='?')
    args = parser.parse_args()

    dry_run = (len(sys.argv) == 2)
    log = open('/var/local/scripts/production/xmlgroomer/log/log', 'a')
    log.write('-'*50 + '\n'+time.strftime("%Y-%m-%d %H:%M:%S   "))

    try:
        f = open(args.beforexml, 'r')
    except IOError, e:
        log.write(e.message)
        log.close()
        sys.exit(e)
        
    # Read file into a char stream and groom it
    char_stream = f.read().decode('utf-8')#.decode('utf-8')
    f.close()

    if not args.error_check:
        for char_stream_groomer in char_stream_groomers:
            char_stream = char_stream_groomer(char_stream)

    try:
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(char_stream.encode('utf-8'), parser)
    except Exception as ee:
        log.write('** error parsing: '+str(ee)+'\n')
        log.close()
        raise
    try: log.write(get_doi(root)+'\n')
    except: log.write('** error getting doi\n')

    if args.error_check:
        for groomer in validators:
            try:
                root = groomer(root)
            except Exception as ee:
                traceback.print_exc()
                print >>sys.stderr, '** error in '+groomer.__name__+': '+str(ee)+'\n'
                output += 'error: error in '+groomer.__name__+': '+str(ee)+'\n'
                log.write('** error in '+groomer.__name__+': '+str(ee)+'\n')

    else:
        for groomer in groomers:
            try:
                root = groomer(root)
            except Exception as ee:
                traceback.print_exc()
                print >>sys.stderr, '** error in '+groomer.__name__+': '+str(ee)+'\n'
                log.write('** error in '+groomer.__name__+': '+str(ee)+'\n')

    if not dry_run and not args.error_check:
        etree.ElementTree(root).write(args.afterxml, xml_declaration=True, encoding='UTF-8')
    else:
        output = output.replace('correction:', 'suggested correction:')

    log.write(output.encode('ascii','ignore'))
    log.close()
    print output.encode('utf-8')
