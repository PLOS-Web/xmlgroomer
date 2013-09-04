#!/usr/bin/env python
# usage: nosetests xmlgroomertest.py

import lxml.etree as etree
import xmlgroomer as x

def verify(before, after, groomer, *args):
    goal = normalize(after)
    result = normalize(etree.tostring(groomer(etree.fromstring(before), *args)))
    if goal != result:
        print 'goal: %r' % goal
        print 'result: %r' % result
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

def test_fix_article_title():
    before = '<article><title-group><title>Bottle\rnose Dolp\nhins</title></title-group></article>'
    after = '<article><title-group><title>Bottlenose Dolphins</title></title-group></article>'
    verify(before, after, x.fix_article_title)

def test_fix_article_title_tags():
    before = '''<article><meta><named-content>hello</named-content></meta><title-group>
        <article-title>Identification of Immunity Related Genes to Study the<named-content content-type="genus-species">
        <named-content content-type="genus"><italic>Physalis</italic></named-content><italic><named-content content-type="species">
        peruviana</named-content></italic></named-content> - <italic><named-content content-type="genus-species">Fusarium oxysporum
        </named-content></italic> pathosystem</article-title></title-group></article>'''
    after = '''<article><meta><named-content>hello</named-content></meta><title-group>
        <article-title>Identification of Immunity Related Genes to Study the<italic>Physalis</italic>
        <italic>peruviana</italic> - <italic>Fusarium oxysporum</italic> pathosystem</article-title></title-group></article>'''
    verify(before, after, x.fix_article_title_tags)

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

def test_fix_corresp_label():
    before = """<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <corresp id="cor1"><label>*</label> E-mail: <email xlink:type="simple">me@example.net</email></corresp>
        </article>"""
    after = """<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <corresp id="cor1">* E-mail: <email xlink:type="simple">me@example.net</email></corresp>
        </article>"""
    verify(before, after, x.fix_corresp_label)

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
    	<article-id pub-id-type="doi">10.1371/journal.pone.0058162</article-id>
        <pub-date pub-type="epub"><day>4</day><month>1</month><year>2012</year></pub-date>
        </article-meta></article>'''
    after = '''<article><article-meta>
    	<article-id pub-id-type="doi">10.1371/journal.pone.0058162</article-id>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        </article-meta></article>'''
    verify(before, after, x.fix_pubdate)

def test_fix_collection():
    before = '''<article><article-meta>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <pub-date pub-type="collection"><month>5</month><year>2009</year></pub-date>
        </article-meta></article>'''
    after = '''<article><article-meta>
        <pub-date pub-type="epub"><day>13</day><month>3</month><year>2013</year></pub-date>
        <pub-date pub-type="collection"><month>3</month><year>2013</year></pub-date>
        </article-meta></article>'''
    verify(before, after, x.fix_collection)

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

def test_fix_elocation():
    before = '''<article><article-meta>
    		<article-id pub-id-type="doi">10.1371/journal.pone.0058162</article-id>
    		<issue>3</issue>
    		</article-meta></article>'''
    after = '''<article><article-meta>
    		<article-id pub-id-type="doi">10.1371/journal.pone.0058162</article-id>
    		<issue>3</issue>
    		<elocation-id>e58162</elocation-id>
   			</article-meta></article>'''
    verify(before, after, x.fix_elocation)

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

def test_fix_xref():
    before = '''<article>
        <xref ref-type="bibr" rid="B3">3</xref>
        <xref ref-type="bibr" rid="B4"/>-
        <xref ref-type="bibr" rid="B5">5</xref>
        </article>'''
    after = '''<article>
        <xref ref-type="bibr" rid="B3">3</xref>-
        <xref ref-type="bibr" rid="B5">5</xref>
        </article>'''
    verify(before, after, x.fix_xref)

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

def test_fix_caption():
    before = '''<article><fig id="pone-0066624-g006" position="float"><label>Figure 6</label>
        <caption><p><bold>Bony labyrinth of<italic>Kulbeckia kulbecke</italic>.</bold></p>
        <p><bold>A</bold>, stereopair and labeled line drawing of digital endocast in anterior view.</p>
        </caption></fig>
        <table-wrap id="tab1" position="float"><label>Table 1</label>
        <caption><p>Summary of border control and vaccination.</p></caption>
        <table/></table-wrap></article>'''
    after = '''<article><fig id="pone-0066624-g006" position="float"><label>Figure 6</label>
        <caption><title><bold>Bony labyrinth of<italic>Kulbeckia kulbecke</italic>.</bold></title>
        <p><bold>A</bold>, stereopair and labeled line drawing of digital endocast in anterior view.</p>
        </caption></fig>
        <table-wrap id="tab1" position="float"><label>Table 1</label>
        <caption><title>Summary of border control and vaccination.</title></caption>
        <table/></table-wrap></article>'''
    verify(before, after, x.fix_caption)

def test_fix_bold():
    before = '''<article><sec id="s3.6"><title><bold>PAPP5</bold> responds to the tetrapyrrole mediated plastid 
        signal and acts as a negative regulator of <bold><italic>PhANG</italic></bold> expression</title></sec>
        <fig id="pone-0066624-g006" position="float"><label>Figure 6</label>
        <caption><title><bold>Bony labyrinth of Kulbeckia kulbecke</bold></title></caption></fig>
        <table-wrap id="tab1" position="float"><label>Table 1</label>
        <caption><title>Summary of border control and <bold>vaccination</bold>.</title></caption>
        <table/></table-wrap></article>'''
    after = '''<article><sec id="s3.6"><title>PAPP5 responds to the tetrapyrrole mediated plastid 
        signal and acts as a negative regulator of <italic>PhANG</italic> expression</title></sec>
        <fig id="pone-0066624-g006" position="float"><label>Figure 6</label>
        <caption><title>Bony labyrinth of Kulbeckia kulbecke</title></caption></fig>
        <table-wrap id="tab1" position="float"><label>Table 1</label>
        <caption><title>Summary of border control and vaccination.</title></caption>
        <table/></table-wrap></article>'''
    verify(before, after, x.fix_bold)

def test_fix_italic():
    before = '''<article><sec id="s3.6"><title><italic>PhANG</italic></title></sec>
        <sec id="s3.6"><title><italic>tetrapyrrole</italic> mediated plastid <italic>PhANG</italic></title></sec>
        <fig id="pone-0066624-g006" position="float"><label>Figure 6</label>
        <caption><title><italic>Bony labyrinth of Kulbeckia kulbecke</italic></title></caption></fig>
        <table-wrap id="tab1" position="float"><label>Table 1</label>
        <caption><title><italic>Summary of border control</italic> and vaccination.</title></caption>
        <table/></table-wrap></article>'''
    after = '''<article><sec id="s3.6"><title>PhANG</title></sec>
        <sec id="s3.6"><title><italic>tetrapyrrole</italic> mediated plastid <italic>PhANG</italic></title></sec>
        <fig id="pone-0066624-g006" position="float"><label>Figure 6</label>
        <caption><title>Bony labyrinth of Kulbeckia kulbecke</title></caption></fig>
        <table-wrap id="tab1" position="float"><label>Table 1</label>
        <caption><title><italic>Summary of border control</italic> and vaccination.</title></caption>
        <table/></table-wrap></article>'''
    verify(before, after, x.fix_italic)

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

def test_fix_null_footnote():
    before = '''<sup><xref rid="ng">3</xref></sup>'''
    after = '''<sup>3</sup>'''
    verify(before, after, x.fix_null_footnote)

def test_fix_target_footnote():
    before = '''<article><table><tbody><tr><td>0.022<xref rid="ngtab1.1">*</xref></td></tr></tbody></table>
        <table-wrap-foot><fn>
        <p>Test or <target id="ngtab1.1" target-type="fn">*</target> exact probability test. NS = not significant.</p>
        </fn></table-wrap-foot></article>'''
    after = '''<article><table><tbody><tr><td>0.022*</td></tr></tbody></table>
        <table-wrap-foot><fn>
        <p>Test or * exact probability test. NS = not significant.</p>
        </fn></table-wrap-foot></article>'''
    verify(before, after, x.fix_target_footnote)

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

def test_fix_merops_link():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <ref><label>2</label><mixed-citation><comment>
        <ext-link xlink:href="http://dx.doi.org/10.1126/science.1103538"></ext-link>
        <ext-link ext-link-type="pmid" xlink:href="http://www.ncbi.nlm.nih.gov/pubmed/15486254"></ext-link>
        </comment></mixed-citation></ref>
        </article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <ref><label>2</label><mixed-citation><comment>
        <ext-link xlink:href="http://dx.doi.org/10.1126/science.1103538" ext-link-type="uri" xlink:type="simple"></ext-link>
        <ext-link ext-link-type="uri" xlink:href="http://www.ncbi.nlm.nih.gov/pubmed/15486254" xlink:type="simple"></ext-link>
        </comment></mixed-citation></ref>
        </article>'''
    verify(before, after, x.fix_merops_link)

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

def test_fix_fn_type():
    before = '<fn id="fn1" fn-type="present-address"><label>a</label><p>Current address</p></fn>'
    after = '<fn id="fn1" fn-type="current-aff"><label>a</label><p>Current address</p></fn>'
    verify(before, after, x.fix_fn_type)

def test_fix_suppressed_tags():
    before = '''<article><award-group><award-id>45902</award-id> </award-group><related-object>H<month/></related-object>
        <roman><italic>P</italic><italic>. troglodytes</italic></roman>_PARG</article>'''
    after = '''<article>45902 H
        <italic>P</italic><italic>. troglodytes</italic>_PARG</article>'''    
    verify(before, after, x.fix_suppressed_tags)

def test_fix_si_title():
    before = '''<sec sec-type="supplementary-material"><title>Supporting Information Legends</title></sec>'''
    after = '''<sec sec-type="supplementary-material"><title>Supporting Information</title></sec>'''
    verify(before, after, x.fix_si_title)

def test_fix_si_captions():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML">
        <supplementary-material xlink:type="simple"><label>Figure S1</label>
        <caption><title>Colocalization.</title><p>Bars.</p><p>(PDF)</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S2</label>
        <caption><title>Colocalization.</title><p>(PDF)</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S3</label>
        <caption><title>Colocalization.</title><p>Bars.</p><p>Another.</p></caption></supplementary-material>
        <supplementary-material xlink:type="simple"><label>Figure S4</label>
        <caption><title>Colocalization.</title></caption></supplementary-material>
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
    verify(before, after, x.fix_si_captions)

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
    message = "error: article xml is missing 'blurb'\n"
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
  <front>
    <article-meta>
      <article-id pub-id-type='doi'>pone.0012345</article-id>
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
  <front>
    <article-meta>
      <article-id pub-id-type='doi'>pone.0012345</article-id>
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
  <front>
    <article-meta>
      <article-id pub-id-type='doi'>pone.0012345</article-id>
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
  <front>
    <article-meta>
      <article-id pub-id-type='doi'>pone.0012345</article-id>
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
    message = "warning: <collab> tag with value: %s.  There may be a missing <on-behalf-of>.\nwarning: <collab> tag with value: %s.  There may be a missing <on-behalf-of>.\n" % (collab, collab)
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
    <p>bad thing</p>
  </funding-statement>
</article>
'''
    message = "error: funding-statement has illegal child node: p\n"
    check(before, message, x.check_improper_children_in_funding_statement)

    before = '''
<article xmlns:xlink="http://www.w3.org/1999/xlink">
  <funding-statement>
    <p>bad thing</p>
    <lala>another bad thing</lala>
  </funding-statement>
</article>
'''
    message = "error: funding-statement has illegal child node: p\nerror: funding-statement has illegal child node: lala\n"
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
     <inline-formula><lala></lala></inline-formula>
     <inline-graphic></inline-graphic>
  </funding-statement>
</article>
'''
    message = ""
    check(before, message, x.check_improper_children_in_funding_statement)
