# PoC (ADK 팀) 진행 내용 및 결과 정리

## 문서 전처리 
![임베딩](./images/preprocessing.jpeg)

## Google ADK(Agent Development Kit)는

- LLM 에이전트를 빠르게 구축하기 위한 Google의 공식 프레임워크
- 핵심 철학은 `선언적 에이전트 정의`로, Python 코드 몇 줄로 에이전트를 정의하고 즉시 실행할 수 있다.
- ADK의 `LlmAgent` 클래스는 **model(사용할 LLM)**, **instruction(에이전트 역할/행동 지침)**, **tools(사용 가능한 도구 목록)** 의 3가지 핵심 속성을 가지며, 이 선언만으로 완전한 에이전트가 생성됨 
- ADK는 LangGraph와 달리 그래프를 직접 구성하지 않고, `sub_agents` 파라미터로 에이전트 간 관계를 선언적으로 정의
  - 이는 빠른 프로토타입에 유리하지만, LangGraph처럼 세밀한 흐름 제어는 제한적임
  - ADK 2.0 에서는 그래프 기반 워크플로가 가능해짐 (라우팅 가능)

```
from google_adk import agent

# tool 정의
def get_weather(location):
    """
    외부 api 호출해 날씨 정보를 가져옴
    """

    # 예시 : 외부 API 호출
    # endpoint = f"https://api.weather.com/v3/wx/conditions?q={location}"
    # response = requests.get(endpoint, params={"api_key": "YOUR_KEY"})
    
    return f"{location}의 현재 날씨는 '매우 맑음', 기온은 24도입니다."

# 에이전트 설정: 똑똑한 비서 고용
weather_bot = agent.LlmAgent(
    model="gemini-2.5-flash",
    instruction="""
    당신은 '스마트 날씨 비서'입니다.
    [규칙]
    - 사용자가 특정 지역의 날씨를 물어보면 'get_weather' 도구를 실행하세요.
    """,
    tools=[get_weather]
)
```

## VertexAI Search
![VertexAI Search](https://docs.cloud.google.com/generative-ai-app-builder/images/generic-search-overview.svg?hl=ko)

웹사이트 데이터와 기타 정형 또는 비정형 데이터가 포함된 애플리케이션에 통합할 수 있는 강력한 Google 품질의 검색 및 콘텐츠 검색 엔진

### 데이터 스토어 (Data Store)

- 검색의 대상이 되는 `원천 데이터의 저장소`
  - 데이터 소스 연결: Google Cloud Storage(GCS), BigQuery, 또는 API를 통한 직접 업로드를 지원
  - 문서 처리: 비정형 데이터(PDF, HTML, TXT)나 정형 데이터(JSON, CSV)를 수집하여 텍스트를 추출하고 분할(Chunking)함
  - 임베딩(Embedding): 텍스트 데이터를 고차원 벡터로 변환하여 벡터 데이터베이스 형태로 인덱싱

### 앱 / 엔진 (App / Engine)

- 데이터 스토어에 씌워지는 검색 엔진
- 하나의 앱(엔진) 에 여러 개의 데이터 스토어를 연결할 수 있음
- App 의 종류
  - Search (검색): 가장 일반적인 형태. 문서나 사이트에서 정보를 찾는데 사용
  - Recommendation (추천): 사용자의 패턴을 학습해 콘텐츠나 상품을 추천
  - Healthcare Search: 의료 데이터(FHIR 등)에 특화된 검색 엔진

### 기능
#### Serving Controls (서빙 컨트롤)
- 기본 AI 모델 판단에만 맡기지 않고, **특정 조건(Condition)** 에 따라 **동작(Action)** 을 강제해 검색 결과를 가공/제어하는 기능
- 대표 유형
  - `Boost`: 조건에 맞는 결과를 상단/하단으로 **순위 조정**
  - `Filter`: 조건에 안 맞는 결과를 **결과에서 제외**
  - `Synonyms`: 서로 다른 단어를 같은 의미로 묶어 **쿼리 확장**
  - `Redirect`: 특정 쿼리는 검색 대신 **지정 URL로 이동**

#### Search Tuning (검색 모델 튜닝)
- 쿼리(Query)별로 “정답으로 기대되는 문서 조각”을 학습시켜, 결과의 **우선순위를 재배치**하는 최적화 과정
- 학습 데이터(요약): `corpus.jsonl`(문서 조각), `queries.jsonl`(질문), `train_labels.tsv`(쿼리-문서 매칭 + `score`: `1` 정답 / `0` 오답)

#### 하이브리드 검색
- Vertex AI Search가 **키워드 검색(정확 일치)** 과 **시맨틱 검색(의미/문맥 유사)** 을 함께 수행하고,
- 각 결과를 **RRF(Reciprocal Rank Fusion)** 로 결합해 최종 랭킹을 결정

#### 파서 (Parsing)
- `Digital Parser`(기본/무료) : 일반 텍스트 추출 중심
- `Layout Parser`(유료) : 문서 구조/계층(제목, 목록, 표, 머리글/각주 등) 인식 (txt파일 지원하지 않음)
- `OCR Parser for PDF`(유료) : 스캔 PDF/이미지 포함 PDF에 최적화. **PDF 전용**, **최대 500페이지**

#### 청킹 (Chunking)
- `LayoutBasedChunking` : 문서 레이아웃(제목, 부제목, 단락, 표 등) 을 인식하고 청킹에서 이를 고려함. 

#### 임베딩
- 기본적으로 Vertex AI Search가 임베딩을 **자동 생성**(대부분은 기본값 권장)
- 이미 자체 임베딩이 있다면 업로드/지정해서 검색에 활용 가능(내부 용어 반영, 사용자 프로필 기반 개인화 등)
- 제약(요약)
  - 대상: **정형 데이터** 또는 **메타데이터가 있는 비정형 데이터**
  - 미지원: **미디어/의료 검색**
  - 형식: 1차원 배열, 차원수 `1~768`
  - 임베딩 키 속성(필드) 최대 2개 태그 가능, **설정 후 삭제 불가**

<!-- <img src="./images/embedding.jpeg" width="600" height="400"> -->
![임베딩](./images/embedding.jpeg)


## 아키텍쳐

![아키텍쳐](./images/adk.jpeg)

## 질답 평가
https://tripodoffice-my.sharepoint.com/:x:/r/personal/whjeong_didim365_com/Documents/NH_POC_%E1%84%8C%E1%85%B5%E1%86%AF%E1%84%83%E1%85%A1%E1%86%B8_%E1%84%85%E1%85%B5%E1%84%89%E1%85%B3%E1%84%90%E1%85%B3_%E1%84%8E%E1%85%B1%E1%84%92%E1%85%A1%E1%86%B8_ADK.xlsx?d=w32dbde53889e47e89d0f159f034c1dd8&csf=1&web=1&e=S1pdIl

## Agent Engine (시간있으면)
- 랭그 랭체이 -> trace logging 이 제한적  (제생각)
- 평가
