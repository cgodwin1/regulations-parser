#vim: set encoding=utf-8
from unittest import TestCase
from regparser.notice import changes
from regparser.tree.struct import Node
from regparser.notice.diff import Amendment


class ChangesTests(TestCase):
    def build_tree(self):
        n1 = Node('n1', label=['200', '1'])
        n2 = Node('n1i', label=['200', 1, 'i'])
        n3 = Node('n2', label=['200', '2'])
        n4 = Node('n3', label=['200', '3'])
        n5 = Node('n3a', label=['200', '3', 'a'])

        n1.children = [n2]
        n4.children = [n5]
        root = Node('root', label=['200'], children=[n1, n3, n4])
        return root

    def test_find_candidate(self):
        root = self.build_tree()
        result = changes.find_candidate(root, 'i')[0]
        self.assertEqual(u'n1i', result.text)

    def test_not_find_candidate(self):
        root = self.build_tree()
        result = changes.find_candidate(root, 'j')
        self.assertEqual(result, [])

    def test_find_misparsed_node(self):
        n2 = Node('n1i', label=['200', 1, 'i'])

        root = self.build_tree()
        result = changes.find_misparsed_node(root, 'i')
        self.assertEqual(result['action'], 'updated')
        self.assertTrue(result['candidate'])
        self.assertEqual(result['node'], n2)

    def test_too_many_candidates(self):
        n1 = Node('n1', label=['200', '1'])
        n2 = Node('n1i', label=['200', 1, 'i'])
        n3 = Node('n2', label=['200', '2'])
        n4 = Node('n3', label=['200', '3'])
        n5 = Node('n3a', label=['200', '3', 'a'])

        n6 = Node('n1ai', label=['200', '1', 'a', 'i'])

        n1.children = [n6, n2]
        n4.children = [n5]
        root = Node('root', label=['200'], children=[n1, n3, n4])

        result = changes.find_misparsed_node(root, 'i')
        self.assertEqual(None, result)

    def test_create_add_amendment(self):
        root = self.build_tree()

        amendment = {'node':root, 'action':'POST'}
        amendments = changes.create_add_amendment(amendment)
        self.assertEqual(6, len(amendments))

        amends = {}
        for a in amendments:
            amends.update(a)
            
        for l in ['200-1-i', '200-1', '200-2', '200-3-a', '200-3', '200']:
            self.assertTrue(l in amends)
   
        for label, node in amends.items():
            self.assertEqual(label, '-'.join(node['node']['label']))
            self.assertEqual(node['action'], 'POST')
            self.assertFalse('children' in node['node'])

    def test_flatten_tree(self):
        tree = self.build_tree()

        node_list = []
        changes.flatten_tree(node_list, tree)

        self.assertEqual(6, len(node_list))
        for n in node_list:
            self.assertEqual(n.children, [])


    def test_remove_intro(self):
        text = 'abcd[text]'
        self.assertEqual('abcd', changes.remove_intro(text))


    def test_resolve_candidates(self):
        amend_map = {}

        n1 = Node('n1', label=['200', '1'])
        amend_map['200-1-a'] =  {'node': n1, 'candidate':False}

        n2 = Node('n2', label=['200', '2', 'i'])
        amend_map['200-2-a-i'] = {'node':n2, 'candidate':True}

        self.assertNotEqual(
            amend_map['200-2-a-i']['node'].label_id(),
            '200-2-a-i')

        changes.resolve_candidates(amend_map)

        self.assertEqual(
            amend_map['200-2-a-i']['node'].label_id(), 
            '200-2-a-i')

    def test_resolve_candidates_accounted_for(self):
        amend_map = {}

        n1 = Node('n1', label=['200', '1'])
        amend_map['200-1-a'] =  {'node': n1, 'candidate':False}

        n2 = Node('n2', label=['200', '2', 'i'])

        amend_map['200-2-a-i'] = {'node':n2, 'candidate':True}
        amend_map['200-2-i'] = {'node':n2, 'candidate':False}

        changes.resolve_candidates(amend_map, warn=False)
        self.assertEqual(2, len(amend_map.keys()))


    def test_match_labels_and_changes_move(self):
        labels_amended = [Amendment('MOVE', '200-1', '200-2')]
        amend_map = changes.match_labels_and_changes(labels_amended, None)
        self.assertEqual(amend_map, {
            '200-1': {'action': 'MOVE', 'destination': ['200', '2']}})

    def test_match_labels_and_changes_delete(self):
        labels_amended = [Amendment('DELETE','200-1-a-i')]
        amend_map = changes.match_labels_and_changes(labels_amended, None)
        self.assertEqual(amend_map, {
            '200-1-a-i':{'action': 'DELETE'}})

    def section_node(self):
        n1 = Node('n2', label=['200', '2'])
        n2 = Node('n2a', label=['200', '2', 'a'])

        n1.children = [n2]
        root = Node('root', label=['200'], children=[n1])
        return root

    def test_match_labels_and_changes(self):
        labels_amended = [Amendment('POST', '200-2'), 
                          Amendment('PUT', '200-2-a')]

        amend_map = changes.match_labels_and_changes(
            labels_amended, self.section_node())

        self.assertEqual(2, len(amend_map.keys()))

        for label, amend in amend_map.items():
            self.assertFalse(amend['candidate'])
            self.assertTrue(amend['action'] in ['POST', 'PUT'])

    def test_match_labels_and_changes_candidate(self):
        labels_amended = [
            Amendment('POST', '200-2'),
            Amendment('PUT', '200-2-a-1-i')]

        n1 = Node('n2', label=['200', '2'])
        n2 = Node('n2a', label=['200', '2', 'i'])

        n1.children = [n2]
        root = Node('root', label=['200'], children=[n1])

        amend_map = changes.match_labels_and_changes(
            labels_amended, root)

        self.assertTrue(amend_map['200-2-a-1-i']['candidate'])
        self.assertTrue(
            amend_map['200-2-a-1-i']['node'].label_id(), '200-2-a-1-i')

