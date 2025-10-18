#!/usr/bin/env python3
"""
Qdrant MCP Server
MCP 프로토콜을 통해 Qdrant 벡터 DB를 사용할 수 있게 해주는 서버
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue
    )
except ImportError:
    print("Error: qdrant-client not installed. Run: pip install qdrant-client", file=sys.stderr)
    sys.exit(1)

# 환경 변수 로드
load_dotenv()


class QdrantServer:
    """Qdrant Vector DB MCP Server"""

    def __init__(self):
        """서버 초기화"""
        # Qdrant 설정 (환경변수 또는 기본값)
        self.host = os.getenv("QDRANT_HOST", "172.28.0.2")
        self.http_port = int(os.getenv("QDRANT_HTTP_PORT", "6333"))
        self.grpc_port = int(os.getenv("QDRANT_GRPC_PORT", "6334"))
        self.prefer_grpc = os.getenv("QDRANT_PREFER_GRPC", "true").lower() == "true"

        # Qdrant 클라이언트 초기화
        try:
            if self.prefer_grpc:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.grpc_port,
                    prefer_grpc=True
                )
            else:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.http_port,
                    prefer_grpc=False
                )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Qdrant: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            # Qdrant health check
            collections = self.client.get_collections()
            return {
                "status": "healthy",
                "host": self.host,
                "port": self.grpc_port if self.prefer_grpc else self.http_port,
                "protocol": "gRPC" if self.prefer_grpc else "HTTP",
                "collections_count": len(collections.collections)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> Dict[str, Any]:
        """
        컬렉션 생성

        Args:
            collection_name: 컬렉션 이름
            vector_size: 벡터 차원
            distance: 거리 메트릭 (Cosine, Euclid, Dot)
        """
        try:
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclid": Distance.EUCLID,
                "Dot": Distance.DOT
            }

            distance_metric = distance_map.get(distance, Distance.COSINE)

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_metric
                )
            )

            return {
                "success": True,
                "collection_name": collection_name,
                "vector_size": vector_size,
                "distance": distance
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def insert_vectors(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        벡터 삽입

        Args:
            collection_name: 컬렉션 이름
            points: 포인트 리스트 [{"id": int, "vector": [...], "payload": {...}}]
        """
        try:
            point_structs = []
            for point in points:
                point_structs.append(
                    PointStruct(
                        id=point.get("id"),
                        vector=point.get("vector"),
                        payload=point.get("payload", {})
                    )
                )

            result = self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )

            return {
                "success": True,
                "inserted_count": len(point_structs),
                "operation_id": result.operation_id if hasattr(result, 'operation_id') else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        벡터 검색

        Args:
            collection_name: 컬렉션 이름
            query_vector: 쿼리 벡터
            limit: 결과 개수
            score_threshold: 점수 임계값
            filter_conditions: 필터 조건
        """
        try:
            # 필터 생성
            search_filter = None
            if filter_conditions:
                # 간단한 필터 지원 (확장 가능)
                field = filter_conditions.get("field")
                value = filter_conditions.get("value")
                if field and value:
                    search_filter = Filter(
                        must=[
                            FieldCondition(
                                key=field,
                                match=MatchValue(value=value)
                            )
                        ]
                    )

            # 검색 실행
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter
            )

            # 결과 변환
            search_results = []
            for result in results:
                search_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })

            return {
                "success": True,
                "results": search_results,
                "count": len(search_results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """컬렉션 삭제"""
        try:
            self.client.delete_collection(collection_name=collection_name)
            return {
                "success": True,
                "collection_name": collection_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def list_collections(self) -> Dict[str, Any]:
        """컬렉션 목록 조회"""
        try:
            collections = self.client.get_collections()
            collection_list = [
                {
                    "name": col.name
                }
                for col in collections.collections
            ]

            return {
                "success": True,
                "collections": collection_list,
                "count": len(collection_list)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """컬렉션 정보 조회"""
        try:
            info = self.client.get_collection(collection_name=collection_name)

            return {
                "success": True,
                "collection_name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP 요청 처리

        Args:
            request: MCP 요청 JSON

        Returns:
            MCP 응답 JSON
        """
        method = request.get("method")
        params = request.get("params", {})

        try:
            # MCP 프로토콜 초기화
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "qdrant-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }

            # Health check
            elif method == "health":
                result = await self.health_check()

            # Collection 생성
            elif method == "create_collection":
                result = await self.create_collection(
                    collection_name=params.get("collection_name"),
                    vector_size=params.get("vector_size"),
                    distance=params.get("distance", "Cosine")
                )

            # Vector 삽입
            elif method == "insert_vectors":
                result = await self.insert_vectors(
                    collection_name=params.get("collection_name"),
                    points=params.get("points", [])
                )

            # Vector 검색
            elif method == "search_vectors":
                result = await self.search_vectors(
                    collection_name=params.get("collection_name"),
                    query_vector=params.get("query_vector"),
                    limit=params.get("limit", 10),
                    score_threshold=params.get("score_threshold"),
                    filter_conditions=params.get("filter")
                )

            # Collection 삭제
            elif method == "delete_collection":
                result = await self.delete_collection(
                    collection_name=params.get("collection_name")
                )

            # Collection 목록
            elif method == "list_collections":
                result = await self.list_collections()

            # Collection 정보
            elif method == "get_collection_info":
                result = await self.get_collection_info(
                    collection_name=params.get("collection_name")
                )

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def run(self):
        """서버 실행 (stdin/stdout 통신)"""
        while True:
            try:
                # stdin에서 요청 읽기
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line.strip())

                # 요청 처리
                response = await self.handle_request(request)

                # stdout으로 응답 전송
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()

            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()


async def main():
    """메인 함수"""
    server = QdrantServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
