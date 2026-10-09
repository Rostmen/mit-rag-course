"""Offline regression tests for graph integrity and matched-budget selection."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from langchain_core.documents import Document
from capstone_checkpoint_4_solution import RetrievalResult
from research_graph import build_graph, AdvancedResearchPaperRetriever


def paper(name,title,authors=None,kind='paper',refs=None):
    return dict(filename=name,title=title,authors=authors or ['Alice'],year=2024,
                document_type=kind,topics=['program synthesis'],methods=[],abstract='',
                metadata_evidence=[{'page':1,'evidence':title}],references=refs or [])


def result(name,text='some actual evidence'):
    return RetrievalResult(Document(page_content=text,metadata={'file_name':name,'page':0}),1,name)


class GraphTests(unittest.TestCase):
    def test_explicit_reference_resolves_and_carries_evidence(self):
        ref={'title':'Target Paper','page':3,'evidence':'See Target Paper for details.'}
        graph,_=build_graph([paper('a','Source',refs=[ref]),paper('b','Target Paper')])
        edges=list(graph.get_edge_data('paper:a','paper:b').values())
        self.assertEqual(edges[0]['edge_type'],'references')
        self.assertEqual(edges[0]['page'],3)

    def test_ungrounded_title_and_external_work_do_not_create_edges(self):
        refs=[{'title':'Target Paper','page':1,'evidence':'Something else'},
              {'title':'External','page':1,'evidence':'External'}]
        graph,_=build_graph([paper('a','Source',refs=refs),paper('b','Target Paper')])
        self.assertFalse(graph.has_edge('paper:a','paper:b'))
        self.assertEqual(graph.graph['unresolved_references'],2)

    def test_versions_require_shared_author_and_exclude_collections(self):
        _,canonical=build_graph([paper('a','Same Title'),paper('b','Same Title'),
                                paper('c','Same Title',authors=['Bob']),
                                paper('d','Same Title',kind='collection')])
        self.assertEqual(canonical['a'],canonical['b'])
        self.assertNotEqual(canonical['a'],canonical['c'])
        self.assertNotEqual(canonical['a'],canonical['d'])

    def test_ambiguous_reference_does_not_resolve(self):
        ref={'title':'Same Title','page':1,'evidence':'Same Title'}
        graph,_=build_graph([paper('a','Source',refs=[ref]),paper('b','Same Title'),
                            paper('c','Same Title',authors=['Bob'])])
        self.assertFalse(graph.has_edge('paper:a','paper:b'))
        self.assertFalse(graph.has_edge('paper:a','paper:c'))

    def test_decomposition_keeps_distinct_aspects_and_budget(self):
        retriever=AdvancedResearchPaperRetriever.__new__(AdvancedResearchPaperRetriever)
        retriever.decompose=lambda q: (['aspect a','aspect b'],{})
        retriever.graph_retriever=Mock(canonical={'a':'a','a-version':'a','b':'b'})
        retriever.hybrid_search=lambda q,k: ([result('b'),result('a')] if q=='aspect b'
                                            else [result('a'),result('a-version')])
        selected=retriever.search('compare','decomposition',2)
        self.assertEqual([r.source for r in selected],['a','b'])
        self.assertEqual(len(selected),2)
        self.assertTrue(all(r.document.page_content=='some actual evidence' for r in selected))

    def test_malformed_planner_falls_back_to_original(self):
        retriever=AdvancedResearchPaperRetriever.__new__(AdvancedResearchPaperRetriever)
        retriever.planner=Mock()
        retriever.planner.invoke.return_value=Mock(content='{"queries": [42]}')
        with tempfile.TemporaryDirectory() as folder:
            retriever.plan_cache=Path(folder)
            queries,trace=retriever.decompose('original question')
        self.assertEqual(queries,['original question'])
        self.assertEqual(trace['fallback'],'ValueError')

    def test_direct_retrieval_takes_priority_over_graph_provenance(self):
        retriever=AdvancedResearchPaperRetriever.__new__(AdvancedResearchPaperRetriever)
        retriever.decompose=lambda q: (['aspect a','aspect b'],{})
        shared=result('shared')
        retriever.hybrid_search=lambda q,k: [] if q=='original' else [shared]
        def expand(query, results):
            role='graph_context' if query=='aspect a' else 'primary'
            return results,{shared.result_id:{'role':role}},[]
        retriever.graph_retriever=Mock(canonical={},expand=expand)
        selected=retriever.search('original','combined',1)
        self.assertEqual(selected[0].document.metadata['retrieval_role'],'primary')
        self.assertEqual(retriever.last_trace['selected'][0]['subquery'],'aspect b')

if __name__=='__main__': unittest.main()
