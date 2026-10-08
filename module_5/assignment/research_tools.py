"""Research-paper equivalents of Lab 5.2's semantic and exact-filter tools.

Tools return original PDF chunks separately from discovery-only metadata.
"""
from __future__ import annotations
import re
import unicodedata
from pydantic import BaseModel, ConfigDict, Field
from langchain_core.tools import StructuredTool
from retrieval_backend import ResearchPaperRetriever, RetrievalResult
from research_graph import build_graph, load_annotations
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL_K = 3


class ToolArgs(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class SearchArgs(ToolArgs):
    query: str = Field(min_length=1, max_length=1600)


class LookupArgs(ToolArgs):
    title: str = Field(default='', max_length=200)
    author: str = Field(default='', max_length=200)
    year: int | None = Field(default=None, ge=1900, le=2100)


class ReadArgs(SearchArgs):
    filename: str = Field(min_length=1, max_length=240)


class ReferenceArgs(ToolArgs):
    filename: str = Field(min_length=1, max_length=240)


def normalized(text):
    return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode().lower()).strip()


class ResearchTools:
    def __init__(self, retriever=None, papers=None):
        self.retriever = retriever if retriever is not None else ResearchPaperRetriever()
        papers = papers if papers is not None else load_annotations(HERE/'annotatedResearchPapers.json')
        self.papers = {p['filename']:p for p in papers}
        self.graph, self.canonical = build_graph(papers)
        self.indices = {}
        for i,doc in enumerate(self.retriever.bm25.documents):
            self.indices.setdefault(doc.metadata['file_name'],[]).append(i)
        self.tools = {
            'retrieve':StructuredTool.from_function(self.retrieve, name='retrieve', args_schema=SearchArgs,
                description='Hybrid BM25/vector search for one focused query; returns up to three PDF passages.'),
            'lookup_papers':StructuredTool.from_function(self.lookup_papers, name='lookup_papers', args_schema=LookupArgs,
                description='Deterministic title/author substring and exact-year filter of the local paper catalogue. Returns discovery metadata, not answer evidence.'),
            'read_paper':StructuredTool.from_function(self.read_paper, name='read_paper', args_schema=ReadArgs,
                description='Read the opening/title passage plus focused BM25 passages within an observed PDF filename; no embedding call.'),
            'follow_references':StructuredTool.from_function(self.follow_references, name='follow_references', args_schema=ReferenceArgs,
                description='List validated in-corpus citation targets of an observed PDF; read target passages before making claims.'),
        }

    def hint(self, name):
        p=self.papers[name]
        return {k:p[k] for k in ['filename','title','authors','year']}

    def retrieve(self, query):
        if not query.strip(): raise ValueError('Empty retrieval query')
        return {'passages':self.retriever.hybrid_search(query, TOOL_K), 'papers':[]}

    def lookup_papers(self, title='', author='', year=None):
        if not title.strip() and not author.strip() and year is None:
            raise ValueError('Supply a title, author, or year filter.')
        found=[]
        for name,p in sorted(self.papers.items()):
            if title and normalized(title) not in normalized(p['title'] or ''): continue
            if author and not any(normalized(author) in normalized(a) for a in p['authors']): continue
            if year is not None and p['year']!=year: continue
            found.append(self.hint(name))
        return {'passages':[], 'papers':found[:8], 'total_matches':len(found),
                'note':'Model-extracted catalogue metadata; verify facts in original PDF passages.'}

    def read_paper(self, filename, query):
        if filename not in self.indices: raise ValueError('Unknown corpus filename')
        ranked=sorted(((self.retriever.bm25.score(query,i),i) for i in self.indices[filename]),reverse=True)
        # Preserve the paper's identity/abstract alongside targeted details. This
        # helps distinguish a named work from generic passages about its field.
        first=self.indices[filename][0]
        selected=[(self.retriever.bm25.score(query,first),first)]
        selected.extend((score,i) for score,i in ranked if score>0 and i!=first)
        results=[RetrievalResult(self.retriever.bm25.documents[i],score,filename)
                 for score,i in selected[:TOOL_K]]
        return {'passages':results,'papers':[]}

    def follow_references(self, filename):
        node='paper:'+filename
        if node not in self.graph: raise ValueError('Unknown corpus filename')
        found=[]; seen=set()
        for _,target,edge in self.graph.out_edges(node,data=True):
            if edge['edge_type']!='references': continue
            name=self.graph.nodes[target]['filename']
            if name in seen:continue
            seen.add(name)
            found.append({**self.hint(name),'reference_page':edge['page'],'reference_quote':edge['evidence']})
        return {'passages':[],'papers':found[:8],'total_matches':len(found),
                'note':'Citation links are discovery hints, not proof of influence or agreement.'}
