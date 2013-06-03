#!/usr/bin/env python
# usage: nosetests xmlgroomertest.py

import lxml.etree as etree
import xmlgroomer as x

def verify(before, after, groomer, *args):
    goal = normalize(after)
    result = normalize(etree.tostring(groomer(etree.fromstring(before), *args)))
    if goal != result:
        print 'goal:\n', goal
        print 'result:\n', result
        assert False

def normalize(string):
    string = ''.join([line.strip() for line in string.split('\n')])
    return etree.tostring(etree.fromstring(string))

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

def test_fix_affiliation():
    before = """<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <contrib xlink:type="simple" contrib-type="author">
        <name name-style="western"><surname>Shaikhali</surname><given-names>Jehad</given-names></name>
        <xref ref-type="aff" rid="aff"/></contrib></article>"""
    after = """<article xmlns:xlink="http://www.w3.org/1999/xlink">
        <contrib xlink:type="simple" contrib-type="author">
        <name name-style="western"><surname>Shaikhali</surname><given-names>Jehad</given-names></name>
        <xref ref-type="aff" rid="aff1"/></contrib></article>"""
    verify(before, after, x.fix_affiliation)

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

def test_fix_journal_ref():
    before = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
    	<ref><label>16</label>
        <mixed-citation publication-type="journal" xlink:type="simple">
        <lpage>516</lpage>doi:
        <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1038/nature03236" xlink:type="simple">
        10.1038/nature03236</ext-link>
        </mixed-citation></ref>
        </article>'''
    after = '''<article xmlns:xlink="http://www.w3.org/1999/xlink">
    	<ref><label>16</label>
        <mixed-citation publication-type="journal" xlink:type="simple">
        <lpage>516</lpage>
        <comment>doi:
        <ext-link ext-link-type="uri" xlink:href="http://dx.doi.org/10.1038/nature03236" xlink:type="simple">
        10.1038/nature03236</ext-link>
        </comment>
        </mixed-citation></ref>
        </article>'''
    verify(before, after, x.fix_journal_ref)

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

def test_fix_empty_element():
    before = '<article><title/><tag><label></label></tag><sec id="s1"></sec><p>Paragraph.</p><body/></article>'
    after = '<article><title/><sec id="s1"></sec><p>Paragraph.</p></article>'
    verify(before, after, x.fix_empty_element)
