from pathlib import Path

from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from agents_v1_sequential.schemas.category_schema import CategoryClassificationOutput
from config.properties import Settings


settings = Settings()

REPO_ROOT = Path(__file__).resolve().parents[2]
CATEGORY_GUIDELINE_PATH = (
    REPO_ROOT / "file" / "agent_knowledge_base_v2" / "category_classification_guideline.md"
)

BASE_INSTRUCTION = """
당신은 질문 라우팅용 카테고리 분류 에이전트다. output_schema(JSON)만 반환한다.

categories에는 반드시 아래 5개 라벨만 사용한다. 상품명·서비스명 등 임의 문자열을 categories 값으로 넣지 않는다.
- retail_loan, corporate_loan, deposit, digital_banking, out_of_scope
out_of_scope는 다른 라벨과 동시에 반환하지 않는다.

분류 대상 질문: conversation_rewrite.rewritten_query가 있으면 그것을, 없으면 state.original_user_query를 쓴다.

세부 판단·복수 카테고리·clarification_needed·clarification_needed_question 채움 규칙은 아래 [카테고리 분류 가이드라인]을 따른다.
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
)
