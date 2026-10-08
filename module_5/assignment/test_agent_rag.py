"""Offline tests exercise the compiled LangGraph transitions and real tool schemas."""
import json
import unittest
from types import SimpleNamespace
from langchain_core.documents import Document
from langchain_core.tools import StructuredTool
import capstone_checkpoint_5_1_agent_rag_starter as agent
from retrieval_backend import RetrievalResult
from research_tools import SearchArgs,LookupArgs,ReadArgs,ReferenceArgs,ResearchTools
from evidence_guard import EvidenceAssessment,validate_assessment,strict_schema


def passage(name='a.pdf',text='Original PDF evidence for subject A.'):
    return RetrievalResult(Document(page_content=text,metadata={'file_name':name,'page':0}),1.0,name)


def plan(action,**kwargs):
    return json.dumps({'action':action,'reasoning':'Test routing decision.',**kwargs})


def analysis(done,queries=None):
    return json.dumps({'done':done,'new_queries':queries or [],'reasoning':'Test evidence gap.'})


class FakeLLM:
    def __init__(self,replies,assessments=None):
        self.replies=iter(replies);self.messages=[]
        self.assessments=iter(assessments) if assessments is not None else None
    def with_structured_output(self,schema,**kwargs):
        assert kwargs==dict(method='json_schema',strict=True,include_raw=True)
        def invoke(messages):
            title=schema['title']
            if title=='TaskChecklist':
                parsed={'requirements':[{'subject':'test','requirement':'Answer the question.'}]}
                raw=SimpleNamespace(content=json.dumps(parsed),usage_metadata={'total_tokens':10})
            elif title.startswith('EvidenceAssessment'):
                payload=json.loads(messages[1].content)
                if self.assessments is not None:
                    assessment=next(self.assessments)
                else:
                    ps=payload['passages']
                    assessment={'requirements':[{'index':1,'covered':bool(ps),
                        'source_ids':[1] if ps else [],'quote':ps[0]['text'] if ps else '',
                        'explanation':'Test evidence.'}],'next_search':''}
                parsed={f'requirement_{i}':item
                        for i,item in enumerate(assessment['requirements'],1)}
                parsed['next_search']=assessment['next_search']
                raw=SimpleNamespace(content=json.dumps(parsed),usage_metadata={'total_tokens':10})
            else:
                raw=self.invoke(messages)
                try:parsed=json.loads(raw.content)
                except ValueError as error:return {'raw':raw,'parsed':None,'parsing_error':error}
            return {'raw':raw,'parsed':parsed,'parsing_error':None}
        return SimpleNamespace(invoke=invoke)
    def invoke(self,messages):
        self.messages.append(messages)
        return SimpleNamespace(content=next(self.replies),usage_metadata={'total_tokens':10})


class FakeTools:
    def __init__(self):
        self.calls=[];self.retriever=self
        specs={
            'retrieve':(self.retrieve,SearchArgs),
            'lookup_papers':(self.lookup,LookupArgs),
            'read_paper':(self.read,ReadArgs),
            'follow_references':(self.references,ReferenceArgs),
        }
        self.tools={name:StructuredTool.from_function(fn,name=name,args_schema=schema,description=name)
                    for name,(fn,schema) in specs.items()}
    def hybrid_search(self,query,k):
        self.calls.append(('retrieve',query))
        return [passage('b.pdf','Missing subject B evidence.') if query=='gap' else passage()]
    def retrieve(self,query):return {'passages':self.hybrid_search(query,3),'papers':[]}
    def lookup(self,title='',author='',year=None):
        self.calls.append(('lookup_papers',title,author,year))
        return {'passages':[],'papers':[{'filename':'b.pdf','title':'Study B','authors':['Author B'],'year':2020}]}
    def read(self,filename,query):
        self.calls.append(('read_paper',filename,query))
        return {'passages':[passage(filename,'Focused subject B evidence.')],'papers':[]}
    def references(self,filename):
        self.calls.append(('follow_references',filename))
        return {'passages':[],'papers':[{'filename':'b.pdf','title':'Study B','authors':[],'year':2020}]}


class GraphTests(unittest.TestCase):
    def test_lab51_actual_graph_loops_after_observation(self):
        tools=FakeTools();llm=FakeLLM([analysis(False,['gap']),analysis(True),'Answer [Source 1] [Source 2].'])
        a=agent.AgenticResearchRetriever(tools,llm);s=a.query('q')
        self.assertEqual([t['node'] for t in s['trace']],['retrieve','analyze','retrieve','analyze','answer_outside_graph'])
        self.assertEqual(len(s['evidence']),2)
        self.assertIn('Missing subject B evidence.',llm.messages[1][1].content)
        self.assertEqual(set(a.graph.get_graph().nodes),{'__start__','retrieve','analyze','__end__'})

    def test_lab51_invalid_json_stops_without_retry(self):
        a=agent.AgenticResearchRetriever(FakeTools(),FakeLLM(['bad JSON','Insufficient evidence.']))
        s=a.query('q');self.assertEqual(s['stop_reason'],'invalid_analysis');self.assertEqual(len(a.meter.calls),2)

    def test_lab51_budget_checked_before_another_model_call(self):
        a=agent.AgenticResearchRetriever(FakeTools(),FakeLLM([analysis(False,['second']),analysis(False,['third']),'Partial answer.']))
        s=a.query('q');self.assertEqual(s['iterations'],3);self.assertEqual(len(a.meter.calls),3)
        self.assertEqual(s['stop_reason'],'retrieval_budget')

    def test_lab51_deduplicates_and_preserves_input_state(self):
        a=agent.AgenticResearchRetriever(FakeTools(),FakeLLM([]));s=agent.initial_state('q')
        result=a.retrieve_node(s)
        self.assertEqual(s['evidence'],{});self.assertEqual(s['iterations'],0)
        self.assertEqual(len(result['evidence']),1)

    def test_lab52_routes_metadata_then_focused_read(self):
        tools=FakeTools();llm=FakeLLM([plan('lookup_papers',title='Study B'),plan('read_paper',filename='b.pdf',query='method'),plan('answer'),'Answer [Source 1].'])
        a=agent.ToolUsingResearchAgent(tools,llm);s=a.query('Find study B methods')
        self.assertEqual([t['node'] for t in s['trace']],['plan','lookup_papers','plan','read_paper','plan','check_coverage','answer'])
        self.assertEqual([c[0] for c in tools.calls],['lookup_papers','read_paper'])
        self.assertIn('Study B',llm.messages[1][1].content)
        self.assertIn('Focused subject B evidence.',llm.messages[2][1].content)

    def test_lab52_selects_followup_after_actual_retrieval(self):
        llm=FakeLLM([plan('retrieve',query='first'),plan('retrieve',query='gap'),plan('answer'),'Both subjects [Source 1] [Source 2].'])
        s=agent.ToolUsingResearchAgent(FakeTools(),llm).query('compare')
        self.assertIn('Original PDF evidence',llm.messages[1][1].content)
        self.assertIn('Missing subject B evidence',llm.messages[2][1].content)
        self.assertEqual(len(s['evidence']),2)

    def test_lab52_rejects_unobserved_filename(self):
        bad=plan('read_paper',filename='../../.env',query='secret')
        tools=FakeTools();a=agent.ToolUsingResearchAgent(tools,FakeLLM([bad,bad,bad,'No evidence.']))
        s=a.query('q');self.assertFalse(tools.calls);self.assertEqual(s['stop_reason'],'invalid_plan')

    def test_lab52_unknown_action_stops_without_retry(self):
        bad=plan('shell',query='bad')
        a=agent.ToolUsingResearchAgent(FakeTools(),FakeLLM([bad,bad,bad,'No evidence.']))
        s=a.query('q');self.assertEqual(s['stop_reason'],'invalid_plan');self.assertEqual(len(a.meter.calls),5)

    def test_missing_optional_explanation_does_not_discard_valid_tool(self):
        tools=FakeTools();llm=FakeLLM(['{"action":"retrieve","query":"gap"}',plan('answer'),'Answer [Source 1].'])
        s=agent.ToolUsingResearchAgent(tools,llm).query('q')
        self.assertEqual(len(tools.calls),1);self.assertEqual(s['stop_reason'],'coverage_complete')

    def test_unused_null_fields_do_not_reject_valid_answer(self):
        a=agent.ToolUsingResearchAgent(FakeTools(),FakeLLM([
            plan('retrieve',query='q',filename=None),
            plan('answer',clarification=None,title='unused '*100),'Answer [Source 1].']))
        s=a.query('q');self.assertEqual(s['stop_reason'],'coverage_complete')

    def test_null_required_tool_argument_is_rejected(self):
        tools=FakeTools();a=agent.ToolUsingResearchAgent(tools,FakeLLM([
            plan('retrieve',query=None),plan('retrieve',query=None),
            plan('retrieve',query=None),'No evidence.']))
        s=a.query('q');self.assertFalse(tools.calls)
        self.assertEqual(s['stop_reason'],'invalid_plan')

    def test_lab52_duplicate_tool_call_stops(self):
        duplicate=plan('retrieve',query='q')
        tools=FakeTools();a=agent.ToolUsingResearchAgent(tools,FakeLLM(
            [duplicate,duplicate,duplicate,duplicate,'Partial.']))
        s=a.query('q');self.assertEqual(len(tools.calls),1);self.assertEqual(s['stop_reason'],'invalid_plan')

    def test_lab52_budget_checked_before_planning(self):
        llm=FakeLLM([plan('retrieve',query=f'q{i}') for i in range(agent.MAX_STEPS)]+['Partial.'])
        a=agent.ToolUsingResearchAgent(FakeTools(),llm);s=a.query('q')
        self.assertEqual(s['iterations'],agent.MAX_STEPS);self.assertEqual(len(a.meter.calls),agent.MAX_STEPS+2)

    def test_chat_clarification_returns_to_plan_with_response(self):
        llm=FakeLLM([plan('retrieve',query='q'),plan('clarify',clarification='Which study?'),plan('retrieve',query='gap'),plan('answer'),'Study B [Source 2].'])
        a=agent.ToolUsingResearchAgent(FakeTools(),llm,input_fn=lambda prompt:'Study B')
        s=a.query('the study',mode='chat')
        self.assertEqual(s['clarification_history'][0]['response'],'Study B')
        self.assertIn('Study B',llm.messages[2][1].content)
        nodes=[t['node'] for t in s['trace']];i=nodes.index('clarify');self.assertEqual(nodes[i+1],'plan')

    def test_batch_clarification_never_blocks(self):
        def unexpected(prompt):raise AssertionError('Batch called input')
        llm=FakeLLM([plan('retrieve',query='q'),plan('clarify',clarification='Which study?'),'Please specify a study.'])
        s=agent.ToolUsingResearchAgent(FakeTools(),llm,input_fn=unexpected).query('q')
        self.assertEqual(s['stop_reason'],'clarification_unavailable')
        self.assertIsNone(s['clarification_history'][0]['response'])

    def test_fresh_batch_state_and_explicit_conversation_history(self):
        llm=FakeLLM([plan('retrieve',query='q'),plan('answer'),'First.',plan('retrieve',query='gap'),plan('answer'),'Second.'])
        a=agent.ToolUsingResearchAgent(FakeTools(),llm)
        a.query('q',history=[{'role':'user','content':'Prior question'}]);s=a.query('second')
        self.assertEqual(len(s['evidence']),1);self.assertEqual(s['conversation_history'],[])
        self.assertEqual(s['trace'][0]['evidence_seen'],0)
        self.assertIn('Prior question',llm.messages[0][1].content)
        self.assertNotIn('Prior question',llm.messages[3][1].content)

    def test_missing_coverage_returns_to_planner_then_new_tool(self):
        checks=[{'requirements':[{'index':1,'covered':False,'source_ids':[],
                 'quote':'','explanation':'Subject B still missing.'}],'next_search':'gap'},
                {'requirements':[{'index':1,'covered':True,'source_ids':[2],
                 'quote':'Missing subject B evidence.','explanation':'Now supported.'}],'next_search':''}]
        llm=FakeLLM([plan('retrieve',query='q'),plan('answer'),plan('retrieve',query='gap'),
                     plan('answer'),'Both [Source 1] [Source 2].'],checks)
        a=agent.ToolUsingResearchAgent(FakeTools(),llm);s=a.query('compare')
        self.assertEqual(s['coverage_checks'],2)
        self.assertEqual(s['stop_reason'],'coverage_complete')
        self.assertIn('Subject B still missing',llm.messages[2][1].content)
        self.assertEqual([t['action'] for t in s['trace'] if t['node']=='check_coverage'],['plan','answer'])

    def test_fabricated_support_quote_does_not_pass_gate(self):
        assessment=EvidenceAssessment.model_validate({'requirements':[{'index':1,'covered':True,
            'source_ids':[1],'quote':'This quote does not exist.','explanation':'claimed support'}],
            'next_search':'missing evidence'})
        gaps=validate_assessment(assessment,[{'subject':'A','requirement':'method'}],
                                 [{'text':'Actual original passage.'}])
        self.assertEqual(len(gaps),1)

    def test_coverage_requires_all_checklist_indices(self):
        assessment=EvidenceAssessment(requirements=[],next_search='')
        with self.assertRaises(ValueError):validate_assessment(assessment,[{'subject':'A','requirement':'method'}],[])

    def test_structured_transport_has_required_fields(self):
        schema=strict_schema(agent.PlanDecision)
        self.assertEqual(set(schema['required']),set(schema['properties']))
        self.assertFalse(schema['additionalProperties'])

    def test_read_paper_keeps_identity_and_targeted_passage(self):
        docs=[Document(page_content='Paper title and abstract',metadata={'file_name':'a.pdf','page':0}),
              Document(page_content='Important requested mechanism',metadata={'file_name':'a.pdf','page':1})]
        retriever=SimpleNamespace(bm25=SimpleNamespace(documents=docs,score=lambda query,i:10*i))
        tools=ResearchTools(retriever,[])
        self.assertEqual([r.document.page_content for r in tools.read_paper('a.pdf','mechanism')['passages']],
                         ['Paper title and abstract','Important requested mechanism'])

    def test_deterministic_catalogue_year_filter(self):
        def paper(name,title,year):
            return {'filename':name,'title':title,'year':year,'authors':['Alice Smith'],'topics':[],
                    'metadata_evidence':[],'references':[],'document_type':'paper'}
        retriever=SimpleNamespace(bm25=SimpleNamespace(documents=[]))
        tools=ResearchTools(retriever,[paper('a.pdf','Study A',2020),paper('b.pdf','Study B',2021)])
        result=tools.tools['lookup_papers'].invoke({'author':'Smith','year':2020})
        self.assertEqual([p['filename'] for p in result['papers']],['a.pdf'])
        self.assertEqual(result['passages'],[])

    def test_citation_range_including_grouped_citations(self):
        result=agent.run_system('q','baseline',FakeTools(),FakeLLM(['Claim [Source 1; Source 99].']))
        self.assertFalse(result['citation_ids_valid'])


if __name__=='__main__':unittest.main()
