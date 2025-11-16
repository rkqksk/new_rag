"""
RAG Prompt Configuration API Routes - v7.4.0
RAG 검색 및 응답 생성을 위한 세부 설정 조정 API
"""

from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field, validator


# ========================================================================
# Enums
# ========================================================================

class SearchMode(str, Enum):
    """Search mode"""
    VECTOR = "vector"              # 벡터 검색만
    KEYWORD = "keyword"            # 키워드 검색만
    HYBRID = "hybrid"              # 하이브리드 검색
    MULTIMODAL = "multimodal"      # 멀티모달 검색 (텍스트 + 이미지)


class RerankingModel(str, Enum):
    """Reranking model"""
    NONE = "none"                  # 리랭킹 없음
    BM25 = "bm25"                  # BM25 기반
    CROSS_ENCODER = "cross_encoder"  # Cross-encoder 모델
    LLM = "llm"                    # LLM 기반 리랭킹


class ResponseStyle(str, Enum):
    """Response style"""
    CONCISE = "concise"            # 간결한 답변
    DETAILED = "detailed"          # 상세한 답변
    TECHNICAL = "technical"        # 기술적 답변
    FRIENDLY = "friendly"          # 친근한 답변
    PROFESSIONAL = "professional"  # 전문적 답변


class CitationStyle(str, Enum):
    """Citation style"""
    NONE = "none"                  # 인용 없음
    INLINE = "inline"              # 인라인 인용 [1], [2]
    FOOTER = "footer"              # 하단 인용
    DETAILED = "detailed"          # 상세 인용 (출처 + 관련도)


# ========================================================================
# Request/Response Models
# ========================================================================

class SearchConfig(BaseModel):
    """Search configuration"""
    mode: SearchMode = Field(SearchMode.HYBRID, description="Search mode")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to retrieve")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")

    # Hybrid search settings
    alpha: float = Field(0.7, ge=0.0, le=1.0, description="Vector weight (1-alpha for keyword)")

    # Reranking settings
    reranking_model: RerankingModel = Field(RerankingModel.CROSS_ENCODER, description="Reranking model")
    rerank_top_k: int = Field(5, ge=1, le=20, description="Top results after reranking")

    # Filters
    filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters")

    # Multimodal settings
    text_weight: float = Field(0.7, ge=0.0, le=1.0, description="Text weight in multimodal search")
    image_weight: float = Field(0.3, ge=0.0, le=1.0, description="Image weight in multimodal search")


class PromptTemplate(BaseModel):
    """Prompt template configuration"""
    system_prompt: str = Field(
        default="""당신은 제조업 제품 전문가입니다. 사용자의 질문에 대해 제공된 컨텍스트를 기반으로 정확하고 유용한 답변을 제공하세요.
답변 시 다음 지침을 따르세요:
1. 컨텍스트에 있는 정보만 사용하세요
2. 확실하지 않으면 "제공된 정보로는 확실하지 않습니다"라고 답하세요
3. 구체적인 제품명, 스펙, 가격 등을 언급하세요
4. 전문 용어는 쉽게 설명하세요""",
        description="System prompt"
    )

    user_template: str = Field(
        default="""질문: {query}

관련 제품 정보:
{context}

위 정보를 바탕으로 질문에 답변해주세요.""",
        description="User prompt template"
    )

    context_template: str = Field(
        default="""제품: {product_name}
카테고리: {category}
가격: {price}원
스펙: {specifications}
설명: {description}
관련도: {score:.2f}
---""",
        description="Context formatting template"
    )

    # Response style
    response_style: ResponseStyle = Field(ResponseStyle.PROFESSIONAL, description="Response style")

    # Citation
    citation_style: CitationStyle = Field(CitationStyle.INLINE, description="Citation style")
    include_sources: bool = Field(True, description="Include source information")


class GenerationConfig(BaseModel):
    """LLM generation configuration"""
    model_name: str = Field("gpt-4", description="LLM model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature (0=deterministic, 2=creative)")
    max_tokens: int = Field(1000, ge=100, le=4000, description="Maximum tokens to generate")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling threshold")
    top_k: int = Field(50, ge=1, le=100, description="Top-k sampling")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stop_sequences: List[str] = Field(default_factory=list, description="Stop sequences")
    stream: bool = Field(False, description="Enable streaming")


class RAGConfig(BaseModel):
    """Complete RAG configuration"""
    config_name: str = Field(..., description="Configuration name")
    description: str = Field("", description="Configuration description")

    search_config: SearchConfig
    prompt_template: PromptTemplate
    generation_config: GenerationConfig

    # Advanced features
    enable_query_expansion: bool = Field(True, description="Enable query expansion")
    enable_context_compression: bool = Field(True, description="Enable context compression")
    enable_answer_validation: bool = Field(True, description="Enable answer validation")
    enable_fallback: bool = Field(True, description="Enable fallback to web search")

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('created_at', 'updated_at', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.now().isoformat()


class RAGConfigPreset(BaseModel):
    """Predefined RAG configuration preset"""
    preset_id: str
    preset_name: str
    description: str
    config: RAGConfig
    is_default: bool = False
    tags: List[str] = Field(default_factory=list)


# ========================================================================
# Predefined Presets
# ========================================================================

PREDEFINED_PRESETS = {
    "default": RAGConfigPreset(
        preset_id="default",
        preset_name="기본 설정",
        description="일반적인 제품 검색 및 응답에 적합한 기본 설정",
        is_default=True,
        tags=["general", "balanced"],
        config=RAGConfig(
            config_name="default",
            description="기본 RAG 설정",
            search_config=SearchConfig(
                mode=SearchMode.HYBRID,
                top_k=10,
                similarity_threshold=0.7,
                alpha=0.7,
                reranking_model=RerankingModel.CROSS_ENCODER,
                rerank_top_k=5
            ),
            prompt_template=PromptTemplate(),
            generation_config=GenerationConfig(
                temperature=0.7,
                max_tokens=1000
            )
        )
    ),

    "precise": RAGConfigPreset(
        preset_id="precise",
        preset_name="정확한 답변",
        description="정확성을 최우선으로 하는 설정 (낮은 temperature, 높은 threshold)",
        tags=["accuracy", "technical"],
        config=RAGConfig(
            config_name="precise",
            description="정확한 답변을 위한 설정",
            search_config=SearchConfig(
                mode=SearchMode.HYBRID,
                top_k=5,
                similarity_threshold=0.85,
                alpha=0.8,
                reranking_model=RerankingModel.CROSS_ENCODER,
                rerank_top_k=3
            ),
            prompt_template=PromptTemplate(
                response_style=ResponseStyle.TECHNICAL,
                citation_style=CitationStyle.DETAILED
            ),
            generation_config=GenerationConfig(
                temperature=0.3,
                max_tokens=800,
                top_p=0.9
            ),
            enable_answer_validation=True
        )
    ),

    "creative": RAGConfigPreset(
        preset_id="creative",
        preset_name="창의적 응답",
        description="창의적이고 다양한 응답을 생성하는 설정 (높은 temperature)",
        tags=["creative", "marketing"],
        config=RAGConfig(
            config_name="creative",
            description="창의적 응답을 위한 설정",
            search_config=SearchConfig(
                mode=SearchMode.HYBRID,
                top_k=15,
                similarity_threshold=0.6,
                alpha=0.6,
                reranking_model=RerankingModel.LLM,
                rerank_top_k=7
            ),
            prompt_template=PromptTemplate(
                response_style=ResponseStyle.FRIENDLY,
                citation_style=CitationStyle.NONE
            ),
            generation_config=GenerationConfig(
                temperature=1.2,
                max_tokens=1500,
                top_p=0.95
            ),
            enable_query_expansion=True
        )
    ),

    "fast": RAGConfigPreset(
        preset_id="fast",
        preset_name="빠른 응답",
        description="속도를 최우선으로 하는 설정 (적은 결과, 간단한 답변)",
        tags=["speed", "concise"],
        config=RAGConfig(
            config_name="fast",
            description="빠른 응답을 위한 설정",
            search_config=SearchConfig(
                mode=SearchMode.VECTOR,
                top_k=3,
                similarity_threshold=0.75,
                reranking_model=RerankingModel.NONE,
                rerank_top_k=3
            ),
            prompt_template=PromptTemplate(
                response_style=ResponseStyle.CONCISE,
                citation_style=CitationStyle.NONE,
                include_sources=False
            ),
            generation_config=GenerationConfig(
                temperature=0.5,
                max_tokens=500,
                stream=False
            ),
            enable_query_expansion=False,
            enable_context_compression=False,
            enable_answer_validation=False
        )
    ),

    "detailed": RAGConfigPreset(
        preset_id="detailed",
        preset_name="상세한 답변",
        description="매우 상세하고 포괄적인 답변을 생성하는 설정",
        tags=["detailed", "comprehensive"],
        config=RAGConfig(
            config_name="detailed",
            description="상세한 답변을 위한 설정",
            search_config=SearchConfig(
                mode=SearchMode.HYBRID,
                top_k=20,
                similarity_threshold=0.65,
                alpha=0.7,
                reranking_model=RerankingModel.CROSS_ENCODER,
                rerank_top_k=10
            ),
            prompt_template=PromptTemplate(
                response_style=ResponseStyle.DETAILED,
                citation_style=CitationStyle.FOOTER,
                include_sources=True
            ),
            generation_config=GenerationConfig(
                temperature=0.7,
                max_tokens=2000,
                top_p=0.9
            ),
            enable_query_expansion=True,
            enable_context_compression=False
        )
    ),

    "multimodal": RAGConfigPreset(
        preset_id="multimodal",
        preset_name="이미지 + 텍스트 검색",
        description="이미지와 텍스트를 함께 검색하는 멀티모달 설정",
        tags=["multimodal", "image"],
        config=RAGConfig(
            config_name="multimodal",
            description="멀티모달 검색을 위한 설정",
            search_config=SearchConfig(
                mode=SearchMode.MULTIMODAL,
                top_k=10,
                similarity_threshold=0.7,
                alpha=0.7,
                text_weight=0.6,
                image_weight=0.4,
                reranking_model=RerankingModel.CROSS_ENCODER,
                rerank_top_k=5
            ),
            prompt_template=PromptTemplate(
                response_style=ResponseStyle.DETAILED,
                citation_style=CitationStyle.INLINE
            ),
            generation_config=GenerationConfig(
                temperature=0.7,
                max_tokens=1200
            )
        )
    )
}


# ========================================================================
# Router
# ========================================================================

class RAGPromptConfigRouter:
    """RAG Prompt Configuration API Router"""

    def __init__(self):
        self.router = APIRouter(prefix="/rag-config", tags=["RAG Configuration"])
        self.custom_configs: Dict[str, RAGConfig] = {}  # User-defined configs
        self.presets: Dict[str, RAGConfigPreset] = PREDEFINED_PRESETS.copy()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        # ================================================================
        # Preset Management
        # ================================================================

        @self.router.get("/presets")
        async def list_presets(tags: Optional[List[str]] = Query(None)):
            """
            List all predefined presets

            사전 정의된 RAG 설정 프리셋 목록

            Presets:
            - default: 기본 설정 (균형잡힌 검색 및 응답)
            - precise: 정확한 답변 (낮은 temperature, 높은 threshold)
            - creative: 창의적 응답 (높은 temperature, 다양한 답변)
            - fast: 빠른 응답 (적은 검색 결과, 간단한 답변)
            - detailed: 상세한 답변 (많은 검색 결과, 긴 답변)
            - multimodal: 이미지 + 텍스트 검색
            """
            presets = list(self.presets.values())

            # Filter by tags
            if tags:
                presets = [p for p in presets if any(tag in p.tags for tag in tags)]

            return {
                "presets": [
                    {
                        "preset_id": p.preset_id,
                        "preset_name": p.preset_name,
                        "description": p.description,
                        "is_default": p.is_default,
                        "tags": p.tags
                    }
                    for p in presets
                ],
                "total": len(presets)
            }

        @self.router.get("/presets/{preset_id}")
        async def get_preset(preset_id: str):
            """
            Get preset details

            특정 프리셋의 상세 설정 조회
            """
            if preset_id not in self.presets:
                raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

            return self.presets[preset_id]

        # ================================================================
        # Custom Configuration Management
        # ================================================================

        @self.router.post("/configs")
        async def create_config(config: RAGConfig):
            """
            Create custom RAG configuration

            사용자 정의 RAG 설정 생성

            Allows fine-tuning:
            - Search parameters (mode, top_k, threshold, reranking)
            - Prompt templates (system, user, context)
            - Generation settings (temperature, max_tokens, etc.)
            - Advanced features (query expansion, compression, validation)
            """
            if config.config_name in self.custom_configs:
                raise HTTPException(status_code=400, detail=f"Config '{config.config_name}' already exists")

            config.created_at = datetime.now().isoformat()
            config.updated_at = config.created_at

            self.custom_configs[config.config_name] = config

            return {
                "status": "created",
                "config": config
            }

        @self.router.get("/configs")
        async def list_configs():
            """
            List all custom configurations

            사용자 정의 RAG 설정 목록
            """
            return {
                "configs": [
                    {
                        "config_name": c.config_name,
                        "description": c.description,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at
                    }
                    for c in self.custom_configs.values()
                ],
                "total": len(self.custom_configs)
            }

        @self.router.get("/configs/{config_name}")
        async def get_config(config_name: str):
            """
            Get configuration details

            특정 설정의 상세 정보 조회
            """
            if config_name not in self.custom_configs:
                raise HTTPException(status_code=404, detail=f"Config '{config_name}' not found")

            return self.custom_configs[config_name]

        @self.router.put("/configs/{config_name}")
        async def update_config(config_name: str, config: RAGConfig):
            """
            Update custom configuration

            사용자 정의 설정 업데이트
            """
            if config_name not in self.custom_configs:
                raise HTTPException(status_code=404, detail=f"Config '{config_name}' not found")

            config.config_name = config_name
            config.updated_at = datetime.now().isoformat()
            config.created_at = self.custom_configs[config_name].created_at

            self.custom_configs[config_name] = config

            return {
                "status": "updated",
                "config": config
            }

        @self.router.delete("/configs/{config_name}")
        async def delete_config(config_name: str):
            """
            Delete custom configuration

            사용자 정의 설정 삭제
            """
            if config_name not in self.custom_configs:
                raise HTTPException(status_code=404, detail=f"Config '{config_name}' not found")

            del self.custom_configs[config_name]

            return {
                "status": "deleted",
                "config_name": config_name
            }

        # ================================================================
        # Configuration Testing
        # ================================================================

        @self.router.post("/test")
        async def test_config(
            config: RAGConfig,
            test_query: str = Body(..., embed=True),
            test_context: Optional[List[Dict[str, Any]]] = Body(None, embed=True)
        ):
            """
            Test RAG configuration with sample query

            RAG 설정 테스트 (샘플 쿼리로 실행)

            Returns:
            - Formatted prompts
            - Search configuration details
            - Generation settings
            - Estimated response time
            """
            # Format prompts with test data
            formatted_system = config.prompt_template.system_prompt

            # Format context
            if test_context:
                formatted_contexts = []
                for ctx in test_context:
                    formatted_ctx = config.prompt_template.context_template.format(
                        product_name=ctx.get("product_name", "N/A"),
                        category=ctx.get("category", "N/A"),
                        price=ctx.get("price", "N/A"),
                        specifications=ctx.get("specifications", "N/A"),
                        description=ctx.get("description", "N/A"),
                        score=ctx.get("score", 0.0)
                    )
                    formatted_contexts.append(formatted_ctx)

                context_str = "\n\n".join(formatted_contexts)
            else:
                context_str = "(테스트 컨텍스트가 제공되지 않았습니다)"

            formatted_user = config.prompt_template.user_template.format(
                query=test_query,
                context=context_str
            )

            # Estimate response time based on config
            estimated_time = self._estimate_response_time(config)

            return {
                "test_query": test_query,
                "formatted_prompts": {
                    "system": formatted_system,
                    "user": formatted_user
                },
                "search_config": config.search_config.dict(),
                "generation_config": config.generation_config.dict(),
                "estimated_response_time_ms": estimated_time,
                "estimated_cost": self._estimate_cost(config),
                "warnings": self._validate_config(config)
            }

        def _estimate_response_time(self, config: RAGConfig) -> float:
            """Estimate response time in milliseconds"""
            base_time = 200  # Base API latency

            # Search time
            search_time = config.search_config.top_k * 5  # 5ms per result
            if config.search_config.reranking_model != RerankingModel.NONE:
                search_time += config.search_config.rerank_top_k * 50  # 50ms per rerank

            # Generation time
            gen_time = config.generation_config.max_tokens * 0.5  # 0.5ms per token

            # Advanced features
            if config.enable_query_expansion:
                base_time += 100
            if config.enable_context_compression:
                base_time += 150
            if config.enable_answer_validation:
                base_time += 200

            return base_time + search_time + gen_time

        def _estimate_cost(self, config: RAGConfig) -> Dict[str, float]:
            """Estimate API cost"""
            # Rough cost estimation (example prices)
            input_tokens = 500 + (config.search_config.rerank_top_k * 100)
            output_tokens = config.generation_config.max_tokens

            # OpenAI GPT-4 pricing example
            input_cost = input_tokens * 0.00003  # $0.03 per 1K tokens
            output_cost = output_tokens * 0.00006  # $0.06 per 1K tokens

            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost_usd": input_cost + output_cost,
                "total_cost_krw": (input_cost + output_cost) * 1300
            }

        def _validate_config(self, config: RAGConfig) -> List[str]:
            """Validate configuration and return warnings"""
            warnings = []

            # Check for inefficient settings
            if config.search_config.top_k > 50:
                warnings.append("⚠️ top_k > 50: 검색 시간이 길어질 수 있습니다")

            if config.generation_config.temperature > 1.5:
                warnings.append("⚠️ temperature > 1.5: 답변 일관성이 낮아질 수 있습니다")

            if config.generation_config.max_tokens > 2000:
                warnings.append("⚠️ max_tokens > 2000: 비용이 많이 발생할 수 있습니다")

            if config.search_config.reranking_model == RerankingModel.LLM:
                warnings.append("⚠️ LLM reranking: 응답 시간이 크게 증가합니다")

            # Check for conflicting settings
            if config.search_config.mode == SearchMode.VECTOR and config.search_config.alpha < 1.0:
                warnings.append("⚠️ Vector 모드에서는 alpha가 의미 없습니다")

            return warnings

        # ================================================================
        # Utility Endpoints
        # ================================================================

        @self.router.get("/defaults")
        async def get_defaults():
            """
            Get default configuration values

            기본 설정 값 조회
            """
            return {
                "search_config": SearchConfig().dict(),
                "prompt_template": PromptTemplate().dict(),
                "generation_config": GenerationConfig().dict()
            }

        @self.router.post("/validate")
        async def validate_config(config: RAGConfig):
            """
            Validate configuration

            설정 검증
            """
            warnings = self._validate_config(config)
            errors = []

            # Check for errors (not just warnings)
            if config.search_config.similarity_threshold > 0.95:
                errors.append("❌ similarity_threshold > 0.95: 결과가 거의 반환되지 않을 수 있습니다")

            if config.generation_config.max_tokens < 100:
                errors.append("❌ max_tokens < 100: 답변이 너무 짧을 수 있습니다")

            is_valid = len(errors) == 0

            return {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "estimated_performance": {
                    "response_time_ms": self._estimate_response_time(config),
                    "cost": self._estimate_cost(config)
                }
            }

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "RAG Prompt Configuration",
                "version": "7.4.0",
                "presets_count": len(self.presets),
                "custom_configs_count": len(self.custom_configs)
            }


def get_rag_prompt_config_router() -> APIRouter:
    """Factory function to create router"""
    router_instance = RAGPromptConfigRouter()
    return router_instance.router
