from unittest import TestCase

from lxml import etree

from regparser.layer import formatting
from regparser.tree.struct import Node


class LayerFormattingTests(TestCase):
    def test_build_header(self):
        xml = etree.fromstring("""
            <BOXHD>
                <CHED H="1">1-1</CHED>
                <CHED H="1">1-2</CHED>
                <CHED H="2">2-1</CHED>
                <CHED H="3">3-1</CHED>
                <CHED H="3">3-2</CHED>
                <CHED H="3">3-3</CHED>
                <CHED H="2">2-2</CHED>
                <CHED H="3">3-4</CHED>
                <CHED H="3">3-5</CHED>
                <CHED H="3">3-6</CHED>
            </BOXHD>""")
        root = formatting.build_header(xml.xpath('./CHED'))

        n11, n12 = root.children
        self.assertEqual('1-1', n11.text)
        self.assertEqual(1, n11.colspan)
        self.assertEqual(3, n11.rowspan)
        self.assertEqual([], n11.children)

        self.assertEqual('1-2', n12.text)
        self.assertEqual(6, n12.colspan)
        self.assertEqual(1, n12.rowspan)

        n21, n22 = n12.children
        self.assertEqual('2-1', n21.text)
        self.assertEqual(3, n21.colspan)
        self.assertEqual(1, n21.rowspan)

        n31, n32, n33 = n21.children
        self.assertEqual('3-1', n31.text)
        self.assertEqual('3-2', n32.text)
        self.assertEqual('3-3', n33.text)
        for n in n21.children:
            self.assertEqual(1, n.colspan)
            self.assertEqual(1, n.rowspan)

        self.assertEqual('2-2', n22.text)
        self.assertEqual(3, n22.colspan)
        self.assertEqual(1, n22.rowspan)

        n34, n35, n36 = n22.children
        self.assertEqual('3-4', n34.text)
        self.assertEqual('3-5', n35.text)
        self.assertEqual('3-6', n36.text)
        for n in n22.children:
            self.assertEqual(1, n.colspan)
            self.assertEqual(1, n.rowspan)

    def test_process(self):
        xml = etree.fromstring("""
            <GPOTABLE>
                <BOXHD>
                    <CHED H="1">1-1</CHED>
                    <CHED H="1">1-2</CHED>
                    <CHED H="2">2-1</CHED>
                    <CHED H="3">3-1</CHED>
                    <CHED H="2">2-2</CHED>
                    <CHED H="3">3-2</CHED>
                    <CHED H="3">3-3</CHED>
                </BOXHD>
                <ROW><ENT>11</ENT><ENT>12</ENT><ENT>13</ENT><ENT>14</ENT></ROW>
                <ROW><ENT>21</ENT><ENT>22</ENT><ENT>23</ENT></ROW>
                <ROW><ENT /><ENT>32</ENT><ENT>33</ENT><ENT>34</ENT></ROW>
            </GPOTABLE>""")
        markdown = formatting.table_xml_to_plaintext(xml)
        node = Node(markdown, source_xml=xml)
        result = formatting.Formatting(None).process(node)
        self.assertEqual(1, len(result))
        result = result[0]

        self.assertEqual(markdown, result['text'])
        self.assertEqual([0], result['locations'])

        mkhd = lambda t, c, r: {'text': t, 'colspan': c, 'rowspan': r}
        data = result['table_data']
        self.assertEqual(
            data['header'],
            [[mkhd('1-1', 1, 3), mkhd('1-2', 3, 1)],
             [mkhd('2-1', 1, 1), mkhd('2-2', 2, 1)],
             [mkhd('3-1', 1, 1), mkhd('3-2', 1, 1), mkhd('3-3', 1, 1)]])
        self.assertEqual(
            data['rows'],
            [['11', '12', '13', '14'],
             ['21', '22', '23'],
             ['', '32', '33', '34']])
