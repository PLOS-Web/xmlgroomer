#!/usr/bin/env python
# -*- coding: utf-8 -*-
# usage: nosetests xmlgroomertest.py


import lxml.etree as etree
import xmlgroomer as x
from lxml import html
from nose import tools


def verify(before, after, groomer, *args):
    goal = normalize(after)
    result = normalize(etree.tostring(groomer(etree.fromstring(before), *args)))
    if goal != result:
        print 'goal: %r' % goal
        print 'result: %r' % result
        assert False


def verify_char_stream(before, after, groomer, *args):
    goal = normalize(after)
    result = normalize(groomer(before), *args)
    if goal != result:
        print 'goal:\n', goal
        print 'result:\n', result
        assert False


def check_char_stream(before, message, groomer):
    x.output = ''
    groomer(before)
    if x.output.strip() != message.strip():
        print 'goal:   %r' % message
        print 'result: %r' % x.output
        assert False


def normalize(string):
    string = ''.join([line.strip() for line in string.split('\n')])
    return etree.tostring(etree.fromstring(string))


def check(before, message, groomer):
    x.output = ''
    groomer(etree.fromstring(before))
    if x.output.strip() != message.strip():
        print 'goal:   %r' % message
        print 'result: %r' % x.output
        assert False


def test_get_singular_node():
    article = "<article><title-group><title>Bottlenose Dolphins</title><year>2013</year><year>2014></year></title-group></article>"
    root = etree.fromstring(article)
    t = x.get_singular_node(root, '//title-group/title')
    tools.eq_(t.text, "Bottlenose Dolphins", "Text not matching")
    tools.eq_(t.tag, "title", "Tag not matching")
    tools.assert_raises(ValueError, x.get_singular_node, root, '//title-group/alt-title')
    tools.assert_raises(ValueError, x.get_singular_node, root, '//title-group/year')


def test_fix_article_type():
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
    verify(before, after, x.fix_article_type)


def test_fix_subject_category():
    before = '''<article><subj-group subj-group-type="heading"><subject>Research Article</subject></subj-group>
        <subj-group subj-group-type="Discipline-v2"><subject>Biology</subject>
        <subj-group><subject>Neuroscience</subject></subj-group></subj-group>
        <subj-group subj-group-type="Discipline-v2"><subject>Medicine</subject>
        <subj-group><subject>Mental health</subject><subj-group><subject>Psychology</subject></subj-group></subj-group></subj-group></article>'''
    after = '<article><subj-group subj-group-type="heading"><subject>Research Article</subject></subj-group></article>'
    verify(before, after, x.fix_subject_category)


def test_fix_article_title():
    before = '<article><title-group><title>Bottle\rnose Dolp\nhins</title></title-group></article>'
    after = '<article><title-group><title>Bottlenose Dolphins</title></title-group></article>'
    verify(before, after, x.fix_article_title)


def test_fix_bad_italic_tags_running_title():
    before = '<article><title-group><alt-title alt-title-type="running-head">&lt;I&gt;Vibrio cholerae&lt;/I&gt; in Kenya</alt-title></title-group></article>'
    after = '<article><title-group><alt-title alt-title-type="running-head"><italic>Vibrio cholerae</italic> in Kenya</alt-title></title-group></article>'
    verify(before, after, x.fix_bad_italic_tags_running_title)


def test_fix_affiliation():
    before = """<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <contrib xlink:type="simple" contrib-type="author">
        <name name-style="western"><surname>Shaikhali</surname><given-names>Jehad</given-names></name>
        <xref ref-type="aff" rid="aff"/></contrib>
        <contrib xlink:type="simple" contrib-type="author">
        <name><surname>Winawer</surname><given-names>Jonathan</given-names></name>
        <xref ref-type="corresp" rid="cor1"/></contrib>
        <aff id="aff1"><label>1</label><addr-line>Institute</addr-line></aff></article>"""
    after = """<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <contrib xlink:type="simple" contrib-type="author">
        <name name-style="western"><surname>Shaikhali</surname><given-names>Jehad</given-names></name>
        <xref ref-type="aff" rid="aff1"/></contrib>
        <contrib xlink:type="simple" contrib-type="author">
        <name><surname>Winawer</surname><given-names>Jonathan</given-names></name>
        <xref ref-type="aff" rid="aff1"/><xref ref-type="corresp" rid="cor1"/></contrib>
        <aff id="aff1"><label>1</label><addr-line>Institute</addr-line></aff></article>"""
    verify(before, after, x.fix_affiliation)


def test_fix_addrline():
    before = """<aff id="aff1"><label>1</label> <addr-line>Institute</addr-line>,</aff>"""
    after = """<aff id="aff1"><label>1</label> <addr-line>Institute</addr-line></aff>"""
    verify(before, after, x.fix_addrline)


def test_fix_corresp_email():
    before = """<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <corresp id="cor1">* E-mail: me@example.net (me)
        you@example.org (you)</corresp></article>"""
    after = """<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <corresp id="cor1">* E-mail: <email xlink:type="simple">me@example.net</email> (me)
        <email xlink:type="simple">you@example.org</email> (you)</corresp></article>"""
    verify(before, after, x.fix_corresp_email)


def test_fix_pubdate():
    before = '''<article><article-meta>
        <article-categories><subj-group subj-group-type="heading">
        <subject>Research Article</subject></subj-group></article-categories>
    	<article-id pub-id-type="doi">10.1371/journal.pone.0058162</article-id>
        <pub-date pub-type="epub"><day>4</day><month>1</month><year>2012</year></pub-date>
        </article-meta></article>'''
    after = '''<article><article-meta>
        <article-categories><subj-group subj-group-type="heading">
        <subject>Research Article</subject></subj-group></article-categories>
    	<article-id pub-id-type="doi">10.1371/journal.pone.0058162</article-id>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        </article-meta></article>'''
    verify(before, after, x.fix_pubdate)


def test_fix_pub_date_elements():
    #test to check and remove month tag in 'collection' if article is PLoS ONE
    before = '''<article><article-meta>
        <journal-title-group><journal-title>PLoS ONE</journal-title></journal-title-group>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <pub-date pub-type="collection"><month>5</month><year>2009</year></pub-date>
        </article-meta></article>'''
    after = '''<article><article-meta>
        <journal-title-group><journal-title>PLoS ONE</journal-title></journal-title-group>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <pub-date pub-type="collection"><year>2013</year></pub-date>
        </article-meta></article>'''
    verify(before, after, x.fix_pub_date_elements)

    #leave month tag in if journal other than PLoS ONE
    before = '''<article><article-meta>
        <journal-title-group><journal-title>PLoS Genetics</journal-title></journal-title-group>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <pub-date pub-type="collection"><month>5</month><year>2009</year></pub-date>
        </article-meta></article>'''
    after = '''<article><article-meta>
        <journal-title-group><journal-title>PLoS Genetics</journal-title></journal-title-group>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <pub-date pub-type="collection"><month>5</month><year>2013</year></pub-date>
        </article-meta></article>'''
    verify(before, after, x.fix_pub_date_elements)

    #test to check for 'collection', if not found, it builds
    before = '''<article><article-meta><author-notes>blah</author-notes>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        </article-meta></article>'''
    after = '''<article><article-meta><author-notes>blah</author-notes>
        <pub-date pub-type="collection"><year>2013</year></pub-date>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        </article-meta></article>'''
    verify(before, after, x.fix_pub_date_elements)

    #test to check for 'ppub', if found, it removes after building 'collection'
    before = '''<article><article-meta><author-notes>blah</author-notes>
        <pub-date pub-type="ppub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        </article-meta></article>'''
    after = '''<article><article-meta><author-notes>blah</author-notes>
        <pub-date pub-type="collection"><year>2013</year></pub-date>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        </article-meta></article>'''
    verify(before, after, x.fix_pub_date_elements)


def test_fix_volume():
    before = '''<article>
        <journal-id journal-id-type="pmc">plosone</journal-id>
        <article-meta>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <volume>6</volume>
        </article-meta>
        </article>'''
    after = '''<article>
        <journal-id journal-id-type="pmc">plosone</journal-id>
        <article-meta>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <volume>8</volume>
        </article-meta>
        </article>'''
    verify(before, after, x.fix_volume)


def test_fix_issue():
    before = '''<article><article-meta>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <issue>6</issue>
        </article-meta></article>'''
    after = '''<article><article-meta>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <issue>3</issue>
        </article-meta></article>'''
    verify(before, after, x.fix_issue)


def test_fix_copyright():
    before = '''<article><article-meta>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <copyright-year>2008</copyright-year>
        </article-meta></article>'''
    after = '''<article><article-meta>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <copyright-year>2013</copyright-year>
        </article-meta></article>'''
    verify(before, after, x.fix_copyright)


def test_add_creative_commons_copyright_link():
    # Adds CC0 4.0 link
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink"><article-meta><permissions>
        <copyright-year>2013</copyright-year><copyright-holder>Cheng, Guggino</copyright-holder>
        <license xlink:type="simple"><license-p>This is an open-access article distributed under 
        the terms of the Creative Commons Attribution License, which permits unrestricted use, 
        distribution, and reproduction in any medium, provided the original author and source are 
        credited.</license-p></license></permissions></article-meta></article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink"><article-meta><permissions>
        <copyright-year>2013</copyright-year><copyright-holder>Cheng, Guggino</copyright-holder>
        <license xlink:type="simple" xlink:href="http://creativecommons.org/licenses/by/4.0/"><license-p>
        This is an open-access article distributed under the terms of the <ext-link ext-link-type="uri" \
        xlink:href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution License</ext-link>, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.
        </license-p></license></permissions></article-meta></article>'''
    verify(before, after, x.add_creative_commons_copyright_link)


    #Adds no link to CC0 Zero
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink"><article-meta><permissions><copyright-year>2013</copyright-year>
        <license><license-p>This is an open-access article, free of all copyright, and may be freely 
        reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any 
        lawful purpose. The work is made available under the Creative Commons CC0 public domain dedication.
        </license-p></license></permissions></article-meta></article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink"><article-meta><permissions><copyright-year>2013</copyright-year>
        <license><license-p>This is an open-access article, free of all copyright, and may be freely 
        reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any 
        lawful purpose. The work is made available under the Creative Commons CC0 public domain dedication.
        </license-p></license></permissions></article-meta></article>'''
    verify(before, after, x.add_creative_commons_copyright_link)


    #CC0 4.0 link present already, groom leaves alone
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink"><article-meta><permissions>
        <copyright-year>2013</copyright-year><copyright-holder>Cheng, Guggino</copyright-holder>
        <license xlink:type="simple" xlink:href="http://creativecommons.org/licenses/by/4.0/"><license-p>
        This is an open-access article distributed under the terms of the <ext-link ext-link-type="uri" \
        xlink:href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution License</ext-link>, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.
        </license-p></license></permissions></article-meta></article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink"><article-meta><permissions>
        <copyright-year>2013</copyright-year><copyright-holder>Cheng, Guggino</copyright-holder>
        <license xlink:type="simple" xlink:href="http://creativecommons.org/licenses/by/4.0/"><license-p>
        This is an open-access article distributed under the terms of the <ext-link ext-link-type="uri" \
        xlink:href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution License</ext-link>, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.
        </license-p></license></permissions></article-meta></article>'''
    verify(before, after, x.add_creative_commons_copyright_link)


def test_fix_elocation():
    before = '''<article><article-meta>
            <article-categories><subj-group subj-group-type="heading">
            <subject>Research Article</subject></subj-group></article-categories>
    		<article-id pub-id-type="doi">10.1371/journal.pone.0058162</article-id>
    		<issue>3</issue>
    		</article-meta></article>'''
    after = '''<article><article-meta>
            <article-categories><subj-group subj-group-type="heading">
            <subject>Research Article</subject></subj-group></article-categories>
    		<article-id pub-id-type="doi">10.1371/journal.pone.0058162</article-id>
    		<issue>3</issue>
    		<elocation-id>e58162</elocation-id>
   			</article-meta></article>'''
    verify(before, after, x.fix_elocation)


def test_fix_fpage_lpage_in_meta():
    before = '<article><article-meta><fpage>000</fpage><lpage>000</lpage></article-meta></article>'
    after = '<article><article-meta></article-meta></article>'
    verify(before, after, x.fix_fpage_lpage_in_meta)

    before = '<article><article-meta><lpage>000</lpage></article-meta></article>'
    after = '<article><article-meta></article-meta></article>'
    verify(before, after, x.fix_fpage_lpage_in_meta)

    before = '<article><article-meta><fpage>000</fpage></article-meta></article>'
    after = '<article><article-meta></article-meta></article>'
    verify(before, after, x.fix_fpage_lpage_in_meta)


def test_fix_related_article():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
            <related-article id="RA1" related-article-type="companion" ext-link-type="uri" \
            vol="" page="e1001434" xlink:type="simple" xlink:href="info:doi/pmed.1001434">
            <article-title>Grand Challenges in Global Mental Health</article-title>
            </related-article>
            </article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
            <related-article id="RA1" related-article-type="companion" ext-link-type="uri" \
            vol="" page="e1001434" xlink:type="simple" xlink:href="info:doi/10.1371/journal.pmed.1001434">
            <article-title>Grand Challenges in Global Mental Health</article-title>
            </related-article>
            </article>'''
    verify(before, after, x.fix_related_article)


def test_fix_title():
    before = '''<article><title>Lipid <title>storage</title> in bulbils.  </title></article>'''
    after = '''<article><title>Lipid <title>storage</title> in bulbils.</title></article>'''
    verify(before, after, x.fix_title)


def test_fix_headed_title():
    before = '''<sec sec-type="headed">
        <title>Purpose:</title>
        <p>To compare the efficacy of extracorporeal shock.</p>
        </sec>'''
    after = '''<sec sec-type="headed">
        <title>Purpose</title>
        <p>To compare the efficacy of extracorporeal shock.</p>
        </sec>'''
    verify(before, after, x.fix_headed_title)


def test_fix_formula():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <fig><caption>
        <disp-formula id ="pcbi.1003016.e001">
        <graphic position="anchor" xlink:href="pcbi.1003016.e001.tif"></graphic>
        </disp-formula>
        </caption></fig>
        <table>
        <disp-formula id ="pcbi.1003016.e002">
        <graphic position="anchor" xlink:href="pcbi.1003016.e002.tif"></graphic>
        </disp-formula>
        </table>
        </article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <fig><caption>
        <inline-formula>
        <inline-graphic xlink:href="pcbi.1003016.e001.tif"></inline-graphic>
        </inline-formula>
        </caption></fig>
        <table>
        <inline-formula>
        <inline-graphic xlink:href="pcbi.1003016.e002.tif"></inline-graphic>
        </inline-formula>
        </table>
        </article>'''
    verify(before, after, x.fix_formula)


def test_fix_formula_label():
    before = '''<article>
        <disp-formula id="eqn1"><label>[Equation 11b]</label></disp-formula>
        <disp-formula id="eqn2"><label>Eq. A hello</label></disp-formula>
        <disp-formula id="eqn3"><label>3 hello</label></disp-formula>
        </article>'''
    after = '''<article>
        <disp-formula id="eqn1"><label>(11b)</label></disp-formula>
        <disp-formula id="eqn2"><label>(A)</label></disp-formula>
        <disp-formula id="eqn3"><label>(3)</label></disp-formula>
        </article>'''
    verify(before, after, x.fix_formula_label)


def test_fix_label():
    before = '''<ref><label><italic>13</italic></label></ref>'''
    after = '''<ref><label>13</label></ref>'''
    verify(before, after, x.fix_label)


def test_fix_url():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <ext-link ext-link-type="uri" xlink:href="10.1023/A:1020  830703012" xlink:type="simple"></ext-link>
        <ext-link ext-link-type="uri" xlink:href="168240 16" xlink:type="simple">16824016</ext-link>
        <ext-link ext-link-type="uri" xlink:href="ftp://example.net/hello" xlink:type="simple">hello</ext-link>
        </article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1023/A:1020830703012" xlink:type="simple"></ext-link>
        <ext-link ext-link-type="uri" xlink:href="http://www.ncbi.nlm.nih.gov/pubmed/16824016" xlink:type="simple">16824016</ext-link>
        <ext-link ext-link-type="uri" xlink:href="ftp://example.net/hello" xlink:type="simple">hello</ext-link>
        </article>'''
    verify(before, after, x.fix_url)


def test_fix_page_range():
    before = '''<ref id="B1"><label>1</label>
        <mixed-citation publication-type="book"><source>Radiobiology for radiobiologists</source>. 
        pp. <fpage>129</fpage>-<lpage>134</lpage>, <fpage>303</fpage>-<lpage>326</lpage>.</mixed-citation></ref>'''
    after = '''<ref id="B1"><label>1</label>
        <mixed-citation publication-type="book"><source>Radiobiology for radiobiologists</source>. 
        pp. <fpage>129</fpage>-<lpage>326</lpage>. </mixed-citation></ref>'''
    verify(before, after, x.fix_page_range)


def test_fix_comment():
    before = '<article><ref><label>2</label><mixed-citation><comment></comment>.</mixed-citation></ref></article>'
    after = '<article><ref><label>2</label><mixed-citation><comment></comment></mixed-citation></ref></article>'
    verify(before, after, x.fix_comment)


def test_fix_provenance():
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
    verify(before, after, x.fix_provenance)


def test_fix_remove_si_label_punctuation():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML">
        <supplementary-material xlink:type="simple"><label>Figure S1.</label>
        <caption><p><bold>Colocalization.</bold> Bars.</p><p>(PDF)</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S2.</label>
        <caption><p><bold>Colocalization.</bold></p><p>(PDF)</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S3.</label>
        <caption><p><bold>Colocalization.</bold> Bars.</p><p>Another.</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S4.</label>
        <caption><p><bold>Colocalization.</bold></p></caption></supplementary-material>
        </article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML">
        <supplementary-material xlink:type="simple"><label>Figure S1</label>
        <caption><p><bold>Colocalization.</bold> Bars.</p><p>(PDF)</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S2</label>
        <caption><p><bold>Colocalization.</bold></p><p>(PDF)</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S3</label>
        <caption><p><bold>Colocalization.</bold> Bars.</p><p>Another.</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S4</label>
        <caption><p><bold>Colocalization.</bold></p></caption></supplementary-material>
        </article>'''


def test_fix_extension():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <supplementary-material id="pone.0063011.s001" xlink:href="pone.0063011.s001" mimetype="image/tiff">
        <label>Figure S1</label>
        <caption><p>(TIFF)</p></caption>
        </supplementary-material></article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <supplementary-material id="pone.0063011.s001" xlink:href="pone.0063011.s001.tiff" mimetype="image/tiff">
        <label>Figure S1</label>
        <caption><p>(TIFF)</p></caption>
        </supplementary-material></article>'''
    verify(before, after, x.fix_extension)


def test_fix_mimetype():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
		<supplementary-material id="pone.0063011.s001" xlink:href="pone.0063011.s001.tiff">
		<label>Figure S1</label>
		<caption><p>(TIFF)</p></caption>
		</supplementary-material></article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
		<supplementary-material id="pone.0063011.s001" xlink:href="pone.0063011.s001.tiff" mimetype="image/tiff">
		<label>Figure S1</label>
		<caption><p>(TIFF)</p></caption>
		</supplementary-material></article>'''
    verify(before, after, x.fix_mimetype)


def test_remove_pua_set():
    before = u'''<p>estrogen stimuli </p>'''
    after = u'''<p>estrogen stimuli </p>'''
    verify_char_stream(before, after, x.remove_pua_set)


def test_check_article_type():
    before = '''<article>
        <article-categories>
        <subj-group subj-group-type="heading">
        <subject>Romantic Comedy</subject>
        </subj-group>
        </article-categories>
        </article>'''
    message = 'error: Romantic Comedy is not a valid article type'
    check(before, message, x.check_article_type)

def test_check_correction_article():
    before = '''<article>
        <article-categories>
        <subj-group subj-group-type="heading">
        <subject>Correction</subject>
        </subj-group>
        </article-categories>
        </article>'''
    message = 'error: no related article element'
    check(before, message, x.check_correction_article)

    before = '''<article>
        <article-categories>
        <subj-group subj-group-type="heading">
        <subject>Correction</subject>
        </subj-group>
        </article-categories>
        <article-meta>
        <related-article related-article-type="article">
        <article-title>Glutamine Supplementation Stimulates Protein-Synthetic</article-title>
        </related-article></article-meta>
        </article>'''
    message = "error: related article type is not 'corrected-article'"
    check(before, message, x.check_correction_article)


def test_check_nlm_ta():
    before = '''<journal-meta><journal-id journal-id-type="nlm-ta">plosone</journal-id></journal-meta>'''
    message = 'error: invalid nlm-ta in metadata: plosone'
    check(before, message, x.check_nlm_ta)


def test_check_misplaced_pullquotes():
    before = '''<body><sec><p><named-content content-type="pullquote">lalala</named-content></p></sec></body>'''
    message = 'warning: pullquote appears as last element of a section\n'
    check(before, message, x.check_misplaced_pullquotes)

    before = '''<body><sec><p></p><p><named-content content-type="pullquote">lalala</named-content></p></sec></body>'''
    message = 'warning: pullquote appears as last element of a section\n'
    check(before, message, x.check_misplaced_pullquotes)

    before = '''<body><sec><p><named-content content-type="pullquote">lalala</named-content></p><p></p></sec></body>'''
    message = ''
    check(before, message, x.check_misplaced_pullquotes)


def test_check_missing_blurbs():
    before = '''
<article>
  <front>
    <journal-meta>
      <journal-id journal-id-type="pmc">plosmed</journal-id>
    </journal-meta>
    <article-meta>
      <abstract abstract-type="toc"></abstract>
    </article-meta>
  </front>
</article>'''
    message = ""
    check(before, message, x.check_missing_blurb)

    before = '''
<article>
  <front>
    <journal-meta>
      <journal-id journal-id-type="pmc">plosmed</journal-id>
    </journal-meta>
    <article-meta>
      <abstract abstract-type="toc">lalala</abstract>
    </article-meta>
  </front>
</article>'''
    message = ""
    check(before, message, x.check_missing_blurb)

    before = '''
<article>
  <front>
    <journal-meta>
      <journal-id journal-id-type="pmc">plosmed</journal-id>
    </journal-meta>
    <article-meta>
    </article-meta>
  </front>
</article>'''
    message = "error: article xml is missing 'blurb'\n"
    check(before, message, x.check_missing_blurb)


def test_check_SI_attributes():
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
<article-categories><subj-group subj-group-type="heading">
        <subject>Research Article</subject></subj-group></article-categories>
  <front>
    <article-meta>
      <article-id pub-id-type='doi'>10.1371/journal.pone.0012345</article-id>
    </article-meta>
  </front>
  <body>
    <sec>
      <supplementary-material mimetype='mime/test' id='pone.0012345.s001' xlink:href='pone.0012345.s001.docx'>
        <label></label>
      </supplementary-material>
    </sec>
  </body>
</article>'''
    message = ''
    check(before, message, x.check_SI_attributes)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
<article-categories><subj-group subj-group-type="heading">
        <subject>Research Article</subject></subj-group></article-categories>
  <front>
    <article-meta>
      <article-id pub-id-type='doi'>10.1371/journal.pone.0012345</article-id>
    </article-meta>
  </front>
  <body>
    <sec>
      <supplementary-material id='pone.0012345.s001' xlink:href='pone.0012345.s001.docx'>
        <label></label>
      </supplementary-material>
    </sec>
  </body>
</article>'''
    message = 'error: mimetype missing: pone.0012345.s001!'
    check(before, message, x.check_SI_attributes)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
<article-categories><subj-group subj-group-type="heading">
        <subject>Research Article</subject></subj-group></article-categories>
  <front>
    <article-meta>
      <article-id pub-id-type='doi'>10.1371/journal.pone.0012345</article-id>
    </article-meta>
  </front>
  <body>
    <sec>
      <supplementary-material mimetype='mime/test' id='pone.0012345.s001' xlink:href='pone.0012345.s001.'>
        <label></label>
      </supplementary-material>
    </sec>
  </body>
</article>'''
    message = 'error: bad or missing file extension: pone.0012345.s001.\n'
    check(before, message, x.check_SI_attributes)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
<article-categories><subj-group subj-group-type="heading">
        <subject>Research Article</subject></subj-group></article-categories>
  <front>
    <article-meta>
      <article-id pub-id-type='doi'>10.1371/journal.pone.0012345</article-id>
    </article-meta>
  </front>
  <body>
    <sec>
      <supplementary-material mimetype='mime/test' id='pone.0011111.s001' xlink:href='pone.0011111.s001.docx'>
        <label></label>
      </supplementary-material>
    </sec>
  </body>
</article>'''
    message = 'error: supp info pone.0011111.s001.docx does not match doi: pone.0012345\n'
    check(before, message, x.check_SI_attributes)


def test_check_lowercase_extensions():
    href = 'lalalal'
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <graphic xlink:href='%s'></graphic>
</article>
''' % href
    message = 'error: bad or missing file extension: %s\n' % href
    check(before, message, x.check_lowercase_extensions)

    href = 'pone.0012345.g001.tif'
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <graphic xlink:href='%s'></graphic>
</article>
''' % href
    message = ''
    check(before, message, x.check_lowercase_extensions)

    href = 'pone.0012345.g001.TIF'
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <graphic xlink:href='%s'></graphic>
</article>
''' % href
    message = 'error: bad or missing file extension: %s\n' % href
    check(before, message, x.check_lowercase_extensions)


def test_check_collab_markup():
    name = "James"
    before = '''
<contrib contrib-type="author">
  <name>
    <surname>%s</surname>
  </name>
</contrib>
''' % name

    message = ""
    check(before, message, x.check_collab_markup)

    name = " of "
    before = '''
<contrib contrib-type="author">
  <name>
    <surname>%s</surname>
  </name>
</contrib>
''' % name

    message = "warning: Article may contain incorrect markup for a collaborative author. Suspicious text to search for: %s\n" % name
    check(before, message, x.check_collab_markup)

    name = " of "
    before = '''
<contrib contrib-type="author">
  <name>
    <given-name>%s</given-name>
  </name>
</contrib>
''' % name

    message = "warning: Article may contain incorrect markup for a collaborative author. Suspicious text to search for: %s\n" % name
    check(before, message, x.check_collab_markup)


def test_on_behalf_of_markup():
    collab = "for"
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <contrib-group>
    <contrib>
       <collab>%s</collab>
    </contrib>
  </contrib-group>
</article>
''' % collab
    message = "warning: <collab> tag with value: %s.  There may be a missing <on-behalf-of>.\n" % collab
    check(before, message, x.check_on_behalf_of_markup)

    collab = "lalala"
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <contrib-group>
    <contrib>
       <collab>%s</collab>
    </contrib>
  </contrib-group>
</article>
''' % collab
    message = ""
    check(before, message, x.check_on_behalf_of_markup)

    collab = "on behalf of"
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <contrib-group>
    <contrib>
       <collab>%s</collab>
       <collab>%s</collab>
    </contrib>
  </contrib-group>
</article>
''' % (collab, collab)
    message = "warning: <collab> tag with value: %s.  There may be a missing <on-behalf-of>.\nwarning: <collab> tag with value: %s.  There may be a missing <on-behalf-of>.\n" % (
        collab, collab)
    check(before, message, x.check_on_behalf_of_markup)


def test_sec_ack_title():
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <sec>
    <title>Acknowledgements</title>
  </sec>
</article>
'''
    message = "warning: there is a <sec> titled \'Acknowledgements\' rather than the use of an <ack> tag."
    check(before, message, x.check_sec_ack_title)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <sec>
    <title>lalala</title>
  </sec>
</article>
'''
    message = ""
    check(before, message, x.check_sec_ack_title)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <sec>
    <title>Acknowledgements</title>
  </sec>
  <sec>
    <title>Acknowledgements</title>
  </sec>
</article>
'''
    message = "warning: there is a <sec> titled \'Acknowledgements\' rather than the use of an <ack> tag.\nwarning: there is a <sec> titled \'Acknowledgements\' rather than the use of an <ack> tag.\n"
    check(before, message, x.check_sec_ack_title)


def test_on_behalf_of_markup():
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <funding-statement>
  </funding-statement>
</article>
'''
    message = ""
    check(before, message, x.check_improper_children_in_funding_statement)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <funding-statement>
    <p>fine thing</p>
  </funding-statement>
</article>
'''
    message = ""
    check(before, message, x.check_improper_children_in_funding_statement)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <funding-statement>
     lala
  </funding-statement>
</article>
'''
    message = ""
    check(before, message, x.check_improper_children_in_funding_statement)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <funding-statement>
     <inline-formula></inline-formula>
  </funding-statement>
</article>
'''
    message = "error: funding-statement has illegal child node: inline-formula\n"
    check(before, message, x.check_improper_children_in_funding_statement)


def test_check_valid_journal_title():
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front>
    <journal-meta>
      <journal-title-group>
        <journal-title>PLoS Biology</journal-title>
      </journal-title-group>
    </journal-meta>
  </front>
</article>
'''
    message = ""
    check(before, message, x.check_valid_journal_title)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front>
    <journal-meta>
      <journal-title-group>
      </journal-title-group>
    </journal-meta>
  </front>
</article>
'''
    message = "error: missing journal title in metadata\n"
    check(before, message, x.check_valid_journal_title)

    bad_journal_name = "bad journal"
    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front>
    <journal-meta>
      <journal-title-group>
        <journal-title>%s</journal-title>
      </journal-title-group>
    </journal-meta>
  </front>
</article>
''' % bad_journal_name
    message = "error: invalid journal title in metadata: %s" % bad_journal_name
    check(before, message, x.check_valid_journal_title)


def test_alert_merops_validator_error():
    before = """\
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front>
    <journal-meta>
      <journal-title-group>
        <journal-title>[!lalalla!]</journal-title>
      </journal-title-group>
    </journal-meta>
  </front>
</article>"""
    message = 'error: located merops-inserted validation error, please address and remove: "     <journal-title>[!lalalla!]</journal"\n'

    check_char_stream(before, message, x.alert_merops_validator_error)

    before = """\
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front>
    <journal-meta>
      <journal-title-group>
        <journal-title>[!(%lalalla%)!]</journal-title>
      </journal-title-group>
    </journal-meta>
  </front>
</article>"""
    message = 'error: located merops-inserted validation error, please address and remove: "     <journal-title>[!(%lalalla%)!]</jou"\n'

    check_char_stream(before, message, x.alert_merops_validator_error)

    before = """\
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <front>
    <journal-meta>
      <journal-title-group>
        <journal-title>[!</journal-title>
      </journal-title-group>
    </journal-meta>
  </front>
</article>"""
    message = ''

    check_char_stream(before, message, x.alert_merops_validator_error)
