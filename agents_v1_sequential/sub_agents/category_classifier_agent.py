from pathlib import Path

from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.callbacks.logging_callbacks import (
    log_after_agent,
    log_after_model,
    log_before_agent,
    log_before_model,
)
from agents_v1_sequential.schemas.category_schema import CategoryClassificationOutput
from config.properties import Settings


settings = Settings()

REPO_ROOT = Path(__file__).resolve().parents[2]
CATEGORY_GUIDELINE_PATH = (
    REPO_ROOT / "file" / "agent_knowledge_base_v2" / "category_classification_guideline.md"
)

BASE_INSTRUCTION = """
당신은 질문 라우팅을 위한 카테고리 분류 에이전트다.
질문을 아래 카테고리로만 분류하고 반드시 JSON 객체로만 응답한다.

카테고리:
- retail_loan
- corporate_loan
- deposit
- digital_banking
- out_of_scope

[입력으로 사용하는 질문]
- conversation_rewrite.rewritten_query가 존재하면, 이를 "실제 분류 대상 질문"으로 사용한다.
- conversation_rewrite가 없으면 state.original_user_query(현재 턴 질문 원문)를 사용한다.

공통 규칙:
1) 분류 기준 질문은 항상 위에서 선택한 "하나의 명확한 질문"이다.
2) 현재 질문이 "이전 답변", "앞에서 말한 내용", "방금 말한 것", "왜 그렇게 답했어",
   "근거가 뭐야" 등 이전 assistant 답변의 이유/근거를 묻는 메타 질문이라면,
   - 가능한 경우 직전 턴의 category_classification.categories 값을 그대로 유지한다고 가정하고,
   - 해당 카테고리를 그대로 다시 반환하는 것을 우선적으로 고려한다.
3) 질문이 문서 카테고리와 직접적으로 관련되면 해당 카테고리만 반환한다. 여러 개면 다중 반환 가능.
4) 문서 카테고리와 관련이 없다고 확실히 판단되는 경우에만 ["out_of_scope"]를 사용한다.
5) out_of_scope와 다른 카테고리를 함께 반환하면 안 된다.
6) 반드시 output_schema 형식을 따른다.
7) 아래 [카테고리 분류 가이드라인]을 우선 기준으로 판단한다.
8) 공통 섹션 질의(평가항목/평가배점/실적산출대상/평점산출방식/실적인정기준/실적제외대상/담당자)는
   out_of_scope가 아니며, 질문에 언급된 평가 영역 카테고리로 분류한다.
9) 공통 섹션 질의인데 카테고리명이 질문에 없어서 카테고리를 특정할 수 없으면:
   - categories는 ["retail_loan", "corporate_loan", "deposit", "digital_banking"]로 반환한다.
   - requires_clarification=true로 반환한다. (사용자에게 평가영역을 확인한다)
   - clarification_question에는 "어느 평가영역(개인여신/기업여신/수신/디지털금융) 기준인가요?"와 같이 한 문장 확인 질문을 작성한다.
10) 그 외 일반 케이스에서는 requires_clarification=false, clarification_question=""로 반환한다.
"""

def load_category_guideline() -> str:
    return CATEGORY_GUIDELINE_PATH.read_text(encoding="utf-8").strip()


category_classifier_agent = LlmAgent(
    name="category_classifier_agent",
    model=settings.GEMINI_MODEL_TYPE_CATEGORY,
    generate_content_config=types.GenerateContentConfig(
        temperature=settings.LLM_TEMPERATURE
    ),
    description="사용자 질문을 NH Best Banker 문서 카테고리로 분류하는 에이전트",
    instruction=f"""
{BASE_INSTRUCTION}

[카테고리 분류 가이드라인]
{load_category_guideline()}
""",
    output_schema=CategoryClassificationOutput,
    output_key="category_classification",
    tools=[],
    before_agent_callback=log_before_agent,
    after_agent_callback=log_after_agent,
    before_model_callback=log_before_model,
    after_model_callback=log_after_model,
)
