"""Question-derived requirements and passage checks for the Lab 5.2 answer gate."""
from __future__ import annotations

import re
import unicodedata
from pydantic import BaseModel, ConfigDict, Field, create_model


class TaskRequirement(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    subject: str = Field(description='Named work or topic explicitly requested by the user.')
    requirement: str = Field(description='One concrete part of the question that the final answer must address.')


class TaskChecklist(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    requirements: list[TaskRequirement]


class RequirementSupport(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    index: int
    covered: bool
    source_ids: list[int]
    quote: str
    explanation: str


class EvidenceAssessment(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    requirements: list[RequirementSupport]
    next_search: str = Field(description='One focused query for the most important remaining evidence gap, or empty if all covered.')


CHECKLIST_PROMPT = '''Convert the user's question into a short checklist of evidence
requirements. Use only what the user asks, not outside knowledge or expected answers.
Create a separate requirement for each requested dimension of each named work.
Use the actual work name as subject where given; otherwise use a short topic phrase.
Do not invent papers, mechanisms, metrics, or requirements not requested.
Do not plan tool calls or queries. Return between 1 and 8 requirements.'''

COVERAGE_PROMPT = '''You are checking whether retrieved PDF passages suffice to
answer a frozen checklist. This is an evidence audit, not an answer-writing task.
For EVERY checklist index, in order, decide whether it is fully covered.
A claim about one paper is NEVER evidence about another named paper. Generic
background about a field is NOT evidence about a particular named method.
Catalogue metadata and reference lists do not establish a work's findings.
For covered=true, supply the IDs of supporting PDF passages and one short EXACT
quotation copied from one of those passages (preserve words; line breaks may vary).
Read the TEXT: do not infer findings from a filename or an expected answer.
If the work is missing or only a requested detail is missing, covered=false,
quote='', and explain precisely what is missing. A relevant keyword is not enough.
Do not say a gap is covered just because other requirements are covered.
When gaps remain, suggest ONE focused semantic search for the missing work/detail.
It must be useful even if the work's exact title or filename is unknown.
Do not write an answer. Return the required structured assessment.'''


def normalized_quote(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode()
    text = re.sub(r'-\s*\n\s*', '', text)
    return re.sub(r'[^a-z0-9]+', '', text.casefold())


def coverage_schema(requirement_count: int):
    """Build a strict response object with one required field per checklist item.

    A variable-length list can be valid JSON while silently omitting a checklist
    item. Fixed object fields let structured output enforce full coverage.
    """
    fields={f'requirement_{index}':(RequirementSupport,...)
            for index in range(1,requirement_count+1)}
    fields['next_search']=(str,...)
    return create_model(f'EvidenceAssessment{requirement_count}',
                        __config__=ConfigDict(extra='forbid',strict=True),**fields)


def unpack_coverage(response, requirement_count: int) -> EvidenceAssessment:
    items=[]
    for index in range(1,requirement_count+1):
        item=getattr(response,f'requirement_{index}')
        # The field name is authoritative; an incorrect generated index cannot
        # reassign evidence to another requirement.
        items.append(item.model_copy(update={'index':index}))
    return EvidenceAssessment(requirements=items,next_search=response.next_search)


def validate_assessment(assessment, requirements, passages):
    """Check completeness of the checklist and provenance of each support quote.

    This validates quote provenance, not semantic entailment. The separate model
    assessment and retained traces expose the remaining semantic uncertainty.
    """
    expected = list(range(1, len(requirements) + 1))
    if [item.index for item in assessment.requirements] != expected:
        raise ValueError('Coverage check must assess every checklist item in order')
    gaps = []
    for item, requirement in zip(assessment.requirements, requirements):
        valid_ids = bool(item.source_ids) and all(1 <= i <= len(passages) for i in item.source_ids)
        quote = normalized_quote(item.quote)
        matched = valid_ids and len(quote) >= 12 and any(
            quote in normalized_quote(passages[i - 1]['text']) for i in item.source_ids
        )
        if not item.covered or not matched:
            reason = item.explanation if not item.covered else 'Supporting quote is missing or not present in the cited passage.'
            gaps.append({'index': item.index, **requirement, 'reason': reason})
    return gaps


def strict_schema(model):
    """Make every transport field required; local Pydantic validation still applies."""
    schema = model.model_json_schema()

    def visit(value):
        if not isinstance(value, dict):
            return
        for key in ['default', 'minLength', 'maxLength', 'minItems', 'maxItems', 'minimum', 'maximum']:
            value.pop(key, None)
        if value.get('type') == 'object':
            value['additionalProperties'] = False
            value['required'] = list(value.get('properties', {}))
        for child in value.values():
            if isinstance(child, dict):
                visit(child)
            elif isinstance(child, list):
                for nested in child:
                    visit(nested)

    visit(schema)
    return schema
