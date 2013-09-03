#!/usr/bin/env python
# usage: xmlgroomer.py before.xml after.xml

import sys
import time
import subprocess
import lxml.etree as etree
import mimetypes
import re

groomers = []
output = ''

def get_doi(root):
    return root.xpath("//article-id[@pub-id-type='doi']")[0].text

def fix_article_type(root):
    global output
    for typ in root.xpath("//article-categories//subj-group[@subj-group-type='heading']/subject"):
        if typ.text == 'Clinical Trial':
            typ.text = 'Research Article'
            output += 'correction: changed article type from Clinical Trial to Research Article\n'
    return root
groomers.append(fix_article_type)

def fix_article_title(root):
    global output
    for title in root.xpath("//title-group/article-title"):
        if re.search(r'[\t\n\r]| {2,}', unicode(title.text)):
            old_title = title.text
            title.text = re.sub(r'[\t\n\r ]+', r' ', unicode(title.text))
            output += 'correction: changed article title from '+old_title+' to '+title.text+'\n'
    return root
groomers.append(fix_article_title)

def fix_article_title_tags(root):
    global output
    title = root.xpath("//title-group/article-title")[0]
    if title.xpath("//named-content"):
        etree.strip_tags(title, 'named-content')
        output += 'correction: removed named-content tags from article title\n' 
    return root
groomers.append(fix_article_title_tags)

def fix_affiliation(root):
    global output
    for author in root.xpath("//contrib[@contrib-type='author']"):
        aff = author.xpath("xref[@ref-type='aff']")
        name = author.xpath("name/surname")[0].text if author.xpath("name/surname") else author.xpath("collab")[0].text
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
            output += 'correction: removed punctuation after addr-line in '+addrline.getparent().attrib['id']+'\n'
    return root
groomers.append(fix_addrline)

def fix_corresp_label(root):
    global output
    for corresp in root.xpath("//corresp"):
        if corresp.xpath("label"):
            etree.strip_tags(corresp, 'label')
            output += 'correction: removed label tag from corresp '+corresp.attrib['id']+'\n'
    return root
groomers.append(fix_corresp_label)

def fix_corresp_email(root):
    global output
    for corresp in root.xpath("//corresp"):
        if not corresp.getchildren():
            email = re.sub(r'(\S+@\S+)', r'<email xlink:type="simple">\1</email>', corresp.text)
            temp = etree.fromstring('<temp xmlns:xlink="http://www.w3.org/1999/xlink">'+email+'</temp>')
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
                    coll.xpath(field)[0].text = pub_val
                    output += 'correction: changed collection '+field+' from '+xml_val+' to '+pub_val+'\n'
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
            old_volume = volume.text
            volume.text = correct_volume
            output += 'correction: changed volume from '+old_volume+' to '+volume.text+'\n'
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
    return root
groomers.append(fix_issue)

def fix_copyright(root):
    global output
    year = root.xpath("//pub-date[@pub-type='epub']/year")[0].text
    for copyright in root.xpath("//article-meta//copyright-year"):
        if copyright.text != year:
            old_copyright = copyright.text
            copyright.text = year
            output += 'correction: changed copyright year from '+old_copyright+' to '+copyright.text+'\n'
    return root
groomers.append(fix_copyright)

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

def fix_xref(root):
    global output
    refnums = ''
    for xref in root.xpath("//xref[@ref-type='bibr']"):
        rid = xref.attrib['rid']
        if not xref.text and rid.startswith('B'):
            if xref.tail:
                if xref.getprevious() is not None:
                    xref.getprevious().tail = (xref.getprevious().tail or '') + xref.tail
                else:
                    xref.getparent().text = (xref.getparent().text or '') + xref.tail
            refnums += rid + ' '
            xref.getparent().remove(xref)
    if refnums:
        output += 'correction: removed closed xref bibr '+refnums+'\n'
    return root
groomers.append(fix_xref)

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

def fix_caption(root):
    global output
    for caption in root.xpath("//fig/caption") + root.xpath("//table-wrap/caption"):
        if not caption.xpath("title") and caption.xpath("p"):
            caption.xpath("p")[0].tag = 'title'
            label = caption.getparent().xpath("label")[0].text
            output += 'correction: changed caption p to title for '+label+'\n'
    return root
groomers.append(fix_caption)

def fix_bold(root):
    global output
    for title in root.xpath("//sec/title") + root.xpath("//fig/caption/title") + root.xpath("//table-wrap/caption/title"):
        if title.xpath("bold"):
            etree.strip_tags(title, 'bold')
            if title.getparent().tag == 'sec':
                label = title.getparent().attrib['id']
            else:
                label = title.getparent().getparent().xpath("label")[0].text
            output += 'correction: removed bold tags from '+label+' title\n'
    return root
groomers.append(fix_bold)

def fix_italic(root):
    global output
    for title in root.xpath("//sec/title") + root.xpath("//fig/caption/title") + root.xpath("//table-wrap/caption/title"):
        if not title.text and title.xpath("italic") and len(title.getchildren())==1 and title.xpath("italic")[0].tail in [None,'.',':','?']:
            etree.strip_tags(title, 'italic')
            if title.getparent().tag == 'sec':
                label = title.getparent().attrib['id']
            else:
                label = title.getparent().getparent().xpath("label")[0].text
            output += 'correction: removed italic tags from '+label+' title\n'
    return root
groomers.append(fix_italic)

def fix_formula(root):
    global output
    for formula in root.xpath("//fig//caption//disp-formula") + root.xpath("//table//disp-formula"):
        formula.tag = 'inline-formula'
        formula.attrib.pop('id')
        graphic = formula.xpath("graphic")[0]
        graphic.tag = 'inline-graphic'
        graphic.attrib.pop('position')
        output += 'correction: changed disp-formula to inline-formula for '+graphic.attrib['{http://www.w3.org/1999/xlink}href']+'\n'
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
groomers.append(fix_formula_label)

def fix_null_footnote(root):
    global output
    for xref in root.xpath("//xref[@rid='ng']"):
        etree.strip_tags(xref.getparent(), 'xref')
        output += "correction: stripped null footnotes (xref rid='ng')\n"
    return root
groomers.append(fix_null_footnote)

def fix_target_footnote(root):
    global output
    for target in root.xpath("//table-wrap-foot/fn/p/target"):
        rid = target.attrib['id']
        for xref in root.xpath("//xref[@rid='"+rid+"']"):
            etree.strip_tags(xref.getparent(), 'xref')
        if target.getparent() is not None:
            etree.strip_tags(target.getparent(), 'target')
        output += "correction: stripped target footnotes and corresponding xref\n"
    return root
groomers.append(fix_target_footnote)

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
    for link in root.xpath("//ext-link"):
        old_link = link.attrib[h]
        # remove whitespace
        if re.search(r'\s', link.attrib[h]):
            link.attrib[h] = re.sub(r'\s', r'', link.attrib[h])
        # prepend http:// if not there
        if not link.attrib[h].startswith('http') and not link.attrib[h].startswith('ftp'):
            link.attrib[h] = 'http://' + link.attrib[h]
        # prepend dx.doi.org/ for doi
        if re.match(r'http://10\.[0-9]{4}', link.attrib[h]):
            link.attrib[h] = link.attrib[h].replace('http://', 'http://dx.doi.org/')
        # prepend www.ncbi.nlm.nih.gov/pubmed/ for pmid
        if re.match(r'http://[0-9]{7,8}$', link.attrib[h]) or link.attrib['ext-link-type'] == 'pmid':
            link.attrib[h] = link.attrib[h].replace('http://', 'http://www.ncbi.nlm.nih.gov/pubmed/')
        if old_link != link.attrib[h]:
            output += 'correction: changed link from '+old_link+' to '+link.attrib[h]+'\n'        
    return root
groomers.append(fix_url)

def fix_merops_link(root):
    global output
    refnums = ''
    for link in root.xpath("//ext-link[@ext-link-type='doi' or @ext-link-type='pmid' or not(@ext-link-type)]"):
        link.attrib['ext-link-type'] = 'uri'
        link.attrib['{http://www.w3.org/1999/xlink}type'] = 'simple'
        refnums += list(link.iterancestors("ref"))[0].xpath("label")[0].text+' '
    if refnums:
        output += 'correction: set ext-link-type=uri and xlink:type=simple in journal references '+refnums+'\n'
    return root
groomers.append(fix_merops_link)

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

def fix_fn_type(root):
    global output
    for fn in root.xpath("//fn[@fn-type='present-address']"):
        fn.attrib['fn-type'] = 'current-aff'
        output += "correction: changed fn-type 'present address' to 'current-aff'\n"
    return root
groomers.append(fix_fn_type)

def fix_suppressed_tags(root):
    global output
    for related in root.xpath("//related-object"):
        for child in related.getchildren():
            if not child.text and not child.getchildren():
                related.remove(child)
    if root.xpath("//roman") or root.xpath("//award-id") or root.xpath("//award-group") + root.xpath("//related-object"):
        etree.strip_tags(root, 'roman', 'award-id', 'award-group', 'related-object')
        output += 'correction: removed suppressed tags (award-id, award-group, roman, related-object)\n'
    return root
groomers.append(fix_suppressed_tags)

def fix_si_title(root):
    global output
    for si_title in root.xpath("//sec[@sec-type='supplementary-material']/title"):
        si_title.text = 'Supporting Information'
        output += 'correction: set supplementary material section title to Supporting Information\n'
    return root
groomers.append(fix_si_title)

def fix_si_captions(root):
    global output
    for title in root.xpath("//supplementary-material/caption/title"):
        label = title.getparent().getparent().xpath("label")[0].text
        paragraphs = title.getparent().xpath("p")
        title.tag = 'bold'
        if not paragraphs or re.match(r'^\(.{1,10}\)$', paragraphs[0].text or ''):
            title.getparent().replace(title, etree.fromstring('<p>'+etree.tostring(title)+'</p>'))
        else:
            ns = '''<p xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML">'''
            new_paragraph = etree.fromstring(etree.tostring(paragraphs[0]).replace(ns, '<p>'+etree.tostring(title)+' '))
            paragraphs[0].getparent().replace(paragraphs[0], new_paragraph)
            title.getparent().remove(title)
        output += 'correction: moved title inside p/bold for '+label+'\n'
    return root
groomers.append(fix_si_captions)

def fix_extension(root):
    global output    
    for si in root.xpath("//supplementary-material"):
        typ = si.xpath("caption/p")[-1].text
        if re.match(r'^\(.*\)$', typ):
            filename = si.attrib['{http://www.w3.org/1999/xlink}href']
            ext = typ.strip('()').lower()
            if re.match(r's[0-9]{3}', filename[-4:]):
                si.attrib['{http://www.w3.org/1999/xlink}href'] = filename+'.'+ext
                output += 'correction: set extension of '+filename+' to '+ext+' for '+si.xpath("label")[0].text+'\n'
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
                output += 'correction: set mimetype of '+typ+' to '+mime+' for '+si.xpath("label")[0].text+'\n'
    return root
groomers.append(fix_mimetype)

def check_article_type(root):
    global output
    article_types = ["Book Review","Book Review/Science in the Media","Community Page","Debate","Editorial",
                     "Education","Essay","Expert Commentary","Expression of Concern","Feature","From Innovation to Application",
                     "Guidelines and Guidance","Health in Action","Historical Profiles and Perspectives",
                     "Historical and Philosophical Perspectives","History/Profile","Interview","Journal Club","Learning Forum",
                     "Message from ISCB","Message from PLoS","Neglected Diseases","Obituary","Online Only: Editorial","Opinion",
                     "Overview","Perspective","Pearls","Photo Quiz","Policy Forum","Policy Platform","Primer","Reader Poll",
                     "Research Article","Research in Translation","Review","Special Report","Symposium","Synopsis",
                     "Technical Report","The PLoS Medicine Debate","Unsolved Mystery","Viewpoints"]
    for typ in root.xpath("//article-categories//subj-group[@subj-group-type='heading']/subject"):
        if typ.text not in article_types:
            output += 'error: '+typ.text+' is not a valid article type\n'
    return root
groomers.append(check_article_type)

def check_misplaced_pullquotes(root):
    raise NotImplementedError("Not done yet.")

def check_missing_blurbs(root):
    raise NotImplementedError("Not done yet.")

def check_SI_attributes(root):
    raise NotImplementedError("Not done yet.")

def check_lowercase_extensions(root):
    raise NotImplementedError("Not done yet.")

def check_collab_markup(root):
    raise NotImplementedError("Not done yet.")

def check_on_behalf_of_markup(root):
    raise NotImplementedError("Not done yet.")

def check_bad_sec_in_acknowledgment(root):
    raise NotImplementedError("Not done yet.")

def check_improper_children_in_funding_statement(root):
    raise NotImplementedError("Not done yet.")

def check_nlm_ta(root):
    global output
    nlm_tas = ["PLoS Biol", "PLoS Comput Biol", "PLoS Clin Trials", "PLoS Genet", "PLoS Med", "PLoS Negl Trop Dis", "PLoS One", "PLoS ONE", "PLoS Pathog", "PLoS Curr"]
    nlm_ta = root.xpath("//journal-meta/journal-id[@journal-id-type='nlm-ta']")
    if not nlm_ta:
        output += 'error: missing nlm-ta in metadata\n'
    elif nlm_ta[0].text not in nlm_tas:
        output += 'error: invalid nlm-ta in metadata: '+nlm_ta[0].text+'\n'
    return root
groomers.append(check_nlm_ta)

def check_valid_journal_title(root):
    raise NotImplementedError("Not done yet.")

if __name__ == '__main__':
    if len(sys.argv) not in [2,3]:
        sys.exit('usage: xmlgroomer.py before.xml after.xml\ndry run: xmlgroomer.py before.xml')
    log = open('/var/local/scripts/production/xmlgroomer/log/log', 'a')
    log.write('-'*50 + '\n'+time.strftime("%Y-%m-%d %H:%M:%S   "))
    try:
        parser = etree.XMLParser(recover = True)
        e = etree.parse(sys.argv[1], parser)
        root = e.getroot()
    except Exception as ee:
        print 'error parsing: '+str(ee)+'\n'
        log.write('** error parsing: '+str(ee)+'\n')
        log.close()
        raise
    try: log.write(get_doi(root)+'\n')
    except: log.write('** error getting doi\n')
    for groomer in groomers:
        try: root = groomer(root)
        except Exception as ee: log.write('** error in '+groomer.__name__+': '+str(ee)+'\n')
    if len(sys.argv) == 3:
        e.write(sys.argv[2], xml_declaration = True, encoding = 'UTF-8')
    else:
        output = output.replace('correction:', 'suggested correction:')
    log.write(output.encode('ascii','ignore'))
    log.close()
    print output
