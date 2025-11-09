"""
사용자 행동 추적기 (Behavior Tracker)
검색, 클릭, 대화, 샘플 신청 데이터 수집
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class BehaviorTracker:
    """
    사용자 행동 추적기

    핵심 기능:
    1. 검색 로그 수집
    2. 클릭 이벤트 추적
    3. 대화 로그 저장
    4. 샘플 신청 기록

    데이터는 DB에 저장되며, DB 연결 실패 시 파일로 백업
    """

    def __init__(self, db_connection=None, backup_dir: str = "logs/analytics"):
        """
        Args:
            db_connection: 데이터베이스 연결 (PostgreSQL)
            backup_dir: DB 실패 시 백업 디렉토리
        """
        self.db = db_connection
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 비동기 큐 (배치 처리)
        self.queue: List[Dict] = []
        self.batch_size = 100
        self.flush_interval_seconds = 60

    async def track_search(
        self,
        user_id: str,
        session_id: str,
        query: str,
        normalized_query: str,
        filters: Dict[str, Any],
        result_count: int,
        result_product_indices: List[str],
        intent: str,
        product_type: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
    ):
        """
        검색 로그 수집

        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            query: 원본 쿼리
            normalized_query: 정규화된 쿼리
            filters: 추출된 필터 {material, capacity, neck_size, etc.}
            result_count: 검색 결과 수
            result_product_indices: 검색된 제품 idx 리스트
            intent: 의도 (search, filter, reference, etc.)
            product_type: 제품 유형 (bottle, pump, cap, etc.)
            response_time_ms: 응답 시간 (밀리초)
            ip_address: IP 주소
        """
        data = {
            "table": "search_logs",
            "data": {
                "user_id": user_id,
                "session_id": session_id,
                "query": query,
                "normalized_query": normalized_query,
                "filters": json.dumps(filters) if filters else None,
                "result_count": result_count,
                "result_product_indices": result_product_indices[:50],  # 최대 50개
                "intent": intent,
                "product_type": product_type,
                "response_time_ms": response_time_ms,
                "ip_address": ip_address,
                "searched_at": datetime.now().isoformat(),
            },
        }

        await self._enqueue(data)

    async def track_click(
        self,
        user_id: str,
        session_id: str,
        product_idx: str,
        product_code: Optional[str],
        product_name: Optional[str],
        category: Optional[str],
        material: Optional[str],
        capacity_ml: Optional[float],
        neck_size: Optional[str],
        click_position: Optional[int],
        search_query: Optional[str],
        referrer: str = "search_result",
        time_on_page_seconds: Optional[int] = None,
        viewed_images: bool = False,
        checked_specs: bool = False,
        checked_compatibility: bool = False,
        requested_sample: bool = False,
        ip_address: Optional[str] = None,
    ):
        """
        클릭 이벤트 추적

        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            product_idx: 제품 idx
            product_code: 제품 코드
            product_name: 제품명
            category: 카테고리 (Bottle, Pump, Cap, etc.)
            material: 재질
            capacity_ml: 용량 (ml)
            neck_size: 네크 사이즈
            click_position: 검색 결과에서 위치 (1-based)
            search_query: 어떤 검색에서 클릭했는지
            referrer: 참조 (search_result, related_products, homepage, etc.)
            time_on_page_seconds: 페이지 체류 시간
            viewed_images: 이미지 확대 여부
            checked_specs: 스펙 탭 클릭 여부
            checked_compatibility: 호환성 확인 여부
            requested_sample: 샘플 신청 여부
            ip_address: IP 주소
        """
        data = {
            "table": "click_logs",
            "data": {
                "user_id": user_id,
                "session_id": session_id,
                "product_idx": product_idx,
                "product_code": product_code,
                "product_name": product_name,
                "category": category,
                "material": material,
                "capacity_ml": capacity_ml,
                "neck_size": neck_size,
                "click_position": click_position,
                "search_query": search_query,
                "referrer": referrer,
                "time_on_page_seconds": time_on_page_seconds,
                "viewed_images": viewed_images,
                "checked_specs": checked_specs,
                "checked_compatibility": checked_compatibility,
                "requested_sample": requested_sample,
                "ip_address": ip_address,
                "clicked_at": datetime.now().isoformat(),
            },
        }

        await self._enqueue(data)

    async def track_conversation(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        bot_response: str,
        intent: str,
        reference_type: Optional[str],
        conversation_state: str,
        focused_product: Optional[str],
        active_filters: Dict[str, Any],
        products_shown: List[str],
        product_count: int,
        action_taken: str,
        response_time_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
    ):
        """
        대화 로그 저장

        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            user_message: 사용자 메시지
            bot_response: 봇 응답
            intent: 의도 (search, filter, reference, compatibility, etc.)
            reference_type: 참조 유형 (number, demonstrative, document, etc.)
            conversation_state: 대화 상태 (GREETING, SEARCHING, FILTERING, etc.)
            focused_product: 포커스된 제품 idx
            active_filters: 활성 필터 상태
            products_shown: 표시된 제품 idx 리스트
            product_count: 표시된 제품 수
            action_taken: 수행된 액션 (search, apply_filter, show_detail, etc.)
            response_time_ms: 응답 시간
            ip_address: IP 주소
        """
        data = {
            "table": "conversation_logs",
            "data": {
                "user_id": user_id,
                "session_id": session_id,
                "user_message": user_message,
                "bot_response": bot_response,
                "intent": intent,
                "reference_type": reference_type,
                "conversation_state": conversation_state,
                "focused_product": focused_product,
                "active_filters": json.dumps(active_filters) if active_filters else None,
                "products_shown": products_shown[:50],  # 최대 50개
                "product_count": product_count,
                "action_taken": action_taken,
                "response_time_ms": response_time_ms,
                "ip_address": ip_address,
                "created_at": datetime.now().isoformat(),
            },
        }

        await self._enqueue(data)

    async def track_sample_request(
        self,
        user_id: str,
        session_id: str,
        product_idx: str,
        product_code: Optional[str],
        product_name: Optional[str],
        category: Optional[str],
        material: Optional[str],
        capacity_ml: Optional[float],
        neck_size: Optional[str],
        intended_use: str,
        company_name: str,
        contact_info: Dict[str, str],
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """
        샘플 신청 기록

        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            product_idx: 제품 idx
            product_code: 제품 코드
            product_name: 제품명
            category: 카테고리
            material: 재질
            capacity_ml: 용량
            neck_size: 네크 사이즈
            intended_use: 용도 (로션, 크림, 세럼, etc.)
            company_name: 회사명
            contact_info: 연락처 {name, phone, email, address}
            notes: 비고
            ip_address: IP 주소
        """
        data = {
            "table": "sample_requests",
            "data": {
                "user_id": user_id,
                "session_id": session_id,
                "product_idx": product_idx,
                "product_code": product_code,
                "product_name": product_name,
                "category": category,
                "material": material,
                "capacity_ml": capacity_ml,
                "neck_size": neck_size,
                "intended_use": intended_use,
                "company_name": company_name,
                "contact_info": json.dumps(contact_info),
                "notes": notes,
                "ip_address": ip_address,
                "requested_at": datetime.now().isoformat(),
                "status": "pending",
            },
        }

        await self._enqueue(data)

        # 샘플 신청은 중요하므로 즉시 플러시
        await self.flush()

    async def _enqueue(self, data: Dict):
        """큐에 데이터 추가"""
        self.queue.append(data)

        # 배치 크기에 도달하면 플러시
        if len(self.queue) >= self.batch_size:
            await self.flush()

    async def flush(self):
        """큐에 있는 데이터를 DB에 저장"""
        if not self.queue:
            return

        batch = self.queue.copy()
        self.queue.clear()

        if self.db:
            # DB에 저장
            try:
                await self._save_to_db(batch)
            except Exception as e:
                print(f"[BehaviorTracker] DB 저장 실패: {e}")
                # DB 실패 시 파일로 백업
                await self._save_to_file(batch)
        else:
            # DB 연결 없으면 파일로 저장
            await self._save_to_file(batch)

    async def _save_to_db(self, batch: List[Dict]):
        """DB에 배치 저장"""
        # 테이블별로 그룹화
        grouped = {}
        for item in batch:
            table = item["table"]
            if table not in grouped:
                grouped[table] = []
            grouped[table].append(item["data"])

        # 각 테이블별로 INSERT
        for table, rows in grouped.items():
            if not rows:
                continue

            # PostgreSQL INSERT 쿼리 생성
            if table == "search_logs":
                await self._insert_search_logs(rows)
            elif table == "click_logs":
                await self._insert_click_logs(rows)
            elif table == "conversation_logs":
                await self._insert_conversation_logs(rows)
            elif table == "sample_requests":
                await self._insert_sample_requests(rows)

    async def _insert_search_logs(self, rows: List[Dict]):
        """검색 로그 INSERT"""
        if not self.db:
            print(f"[BehaviorTracker] No DB connection - skipping {len(rows)} search logs")
            return

        try:
            # Execute SQL insert with SQLAlchemy
            sql = """
                INSERT INTO search_logs (
                    user_id, session_id, query, normalized_query, filters,
                    result_count, result_product_indices, intent, product_type,
                    response_time_ms, ip_address, searched_at
                ) VALUES (
                    :user_id, :session_id, :query, :normalized_query, :filters,
                    :result_count, :result_product_indices, :intent, :product_type,
                    :response_time_ms, :ip_address, :searched_at
                )
            """
            await asyncio.to_thread(self.db.execute, sql, rows)
            await asyncio.to_thread(self.db.commit)
            print(f"[BehaviorTracker] Inserted {len(rows)} search logs")
        except Exception as e:
            print(f"[BehaviorTracker] Failed to insert search logs: {e}")
            await asyncio.to_thread(self.db.rollback)

    async def _insert_click_logs(self, rows: List[Dict]):
        """클릭 로그 INSERT"""
        if not self.db:
            print(f"[BehaviorTracker] No DB connection - skipping {len(rows)} click logs")
            return

        try:
            sql = """
                INSERT INTO click_logs (
                    user_id, session_id, product_idx, product_code, product_name,
                    category, material, capacity_ml, position, source_query,
                    clicked_at
                ) VALUES (
                    :user_id, :session_id, :product_idx, :product_code, :product_name,
                    :category, :material, :capacity_ml, :position, :source_query,
                    :clicked_at
                )
            """
            await asyncio.to_thread(self.db.execute, sql, rows)
            await asyncio.to_thread(self.db.commit)
            print(f"[BehaviorTracker] Inserted {len(rows)} click logs")
        except Exception as e:
            print(f"[BehaviorTracker] Failed to insert click logs: {e}")
            await asyncio.to_thread(self.db.rollback)

    async def _insert_conversation_logs(self, rows: List[Dict]):
        """대화 로그 INSERT"""
        if not self.db:
            print(f"[BehaviorTracker] No DB connection - skipping {len(rows)} conversation logs")
            return

        try:
            sql = """
                INSERT INTO conversation_logs (
                    user_id, session_id, message_id, role, content,
                    intent, extracted_entities, response_time_ms, model_used,
                    created_at
                ) VALUES (
                    :user_id, :session_id, :message_id, :role, :content,
                    :intent, :extracted_entities, :response_time_ms, :model_used,
                    :created_at
                )
            """
            await asyncio.to_thread(self.db.execute, sql, rows)
            await asyncio.to_thread(self.db.commit)
            print(f"[BehaviorTracker] Inserted {len(rows)} conversation logs")
        except Exception as e:
            print(f"[BehaviorTracker] Failed to insert conversation logs: {e}")
            await asyncio.to_thread(self.db.rollback)

    async def _insert_sample_requests(self, rows: List[Dict]):
        """샘플 신청 INSERT"""
        if not self.db:
            print(f"[BehaviorTracker] No DB connection - skipping {len(rows)} sample requests")
            return

        try:
            sql = """
                INSERT INTO sample_requests (
                    user_id, session_id, product_idx, product_code, product_name,
                    customer_name, customer_email, customer_phone, company_name,
                    quantity, message, status, requested_at
                ) VALUES (
                    :user_id, :session_id, :product_idx, :product_code, :product_name,
                    :customer_name, :customer_email, :customer_phone, :company_name,
                    :quantity, :message, :status, :requested_at
                )
            """
            await asyncio.to_thread(self.db.execute, sql, rows)
            await asyncio.to_thread(self.db.commit)
            print(f"[BehaviorTracker] Inserted {len(rows)} sample requests")
        except Exception as e:
            print(f"[BehaviorTracker] Failed to insert sample requests: {e}")
            await asyncio.to_thread(self.db.rollback)

    async def _save_to_file(self, batch: List[Dict]):
        """파일로 백업 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_{timestamp}.jsonl"

        with open(backup_file, "w", encoding="utf-8") as f:
            for item in batch:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(f"[BehaviorTracker] Backed up {len(batch)} records to {backup_file}")

    async def start_auto_flush(self):
        """자동 플러시 시작 (백그라운드 태스크)"""
        while True:
            await asyncio.sleep(self.flush_interval_seconds)
            await self.flush()


# 싱글톤 인스턴스
_tracker_instance = None


def get_behavior_tracker(db_connection=None) -> BehaviorTracker:
    """싱글톤 행동 추적기 반환"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = BehaviorTracker(db_connection=db_connection)
    return _tracker_instance
