"""SQLite Usage Storage (Step 3: Cost Tracking)"""

import asyncio
from datetime import datetime

import aiosqlite

from src.domain.entities.usage import Usage
from src.domain.ports.outbound.usage_port import UsageStoragePort


class SqliteUsageStorage(UsageStoragePort):
    """
    SQLite 기반 Usage 저장소

    LLM 호출 사용량 및 비용 데이터를 SQLite에 저장하고 조회합니다.
    동시성 처리: WAL 모드 + 쓰기 Lock
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """데이터베이스 초기화 (테이블 생성 + WAL 모드)"""
        if self._initialized:
            return

        conn = await self._get_connection()

        # WAL 모드 활성화 (동시 읽기/쓰기 지원)
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA busy_timeout=5000")

        # usage 테이블 생성
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 월별 조회를 위한 인덱스
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_created_at
            ON usage(created_at)
        """)

        # 모델별 조회를 위한 인덱스
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_model
            ON usage(model)
        """)

        await conn.commit()
        self._initialized = True

    async def _get_connection(self) -> aiosqlite.Connection:
        """싱글톤 연결 반환"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self._db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def save_usage(self, usage: Usage) -> None:
        """사용량 데이터 저장"""
        async with self._write_lock:
            conn = await self._get_connection()
            await conn.execute(
                """INSERT INTO usage (model, prompt_tokens, completion_tokens, total_tokens, cost_usd, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    usage.model,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.total_tokens,
                    usage.cost_usd,
                    usage.created_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_monthly_total(self, year: int, month: int) -> float:
        """특정 월의 총 비용 조회 (USD)"""
        conn = await self._get_connection()

        # 해당 월의 시작일과 종료일 계산
        start_date = datetime(year, month, 1)
        end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

        async with conn.execute(
            """SELECT SUM(cost_usd) as total
               FROM usage
               WHERE created_at >= ? AND created_at < ?""",
            (start_date.isoformat(), end_date.isoformat()),
        ) as cursor:
            row = await cursor.fetchone()
            return row["total"] if row["total"] is not None else 0.0

    async def get_usage_by_model(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, float]:
        """기간별 모델별 비용 조회"""
        conn = await self._get_connection()

        async with conn.execute(
            """SELECT model, SUM(cost_usd) as total_cost
               FROM usage
               WHERE created_at >= ? AND created_at <= ?
               GROUP BY model""",
            (start_date.isoformat(), end_date.isoformat()),
        ) as cursor:
            rows = await cursor.fetchall()
            return {row["model"]: row["total_cost"] for row in rows}

    async def get_usage_summary(self, start_date: datetime, end_date: datetime) -> dict:
        """기간별 사용량 요약"""
        conn = await self._get_connection()

        # 총 비용, 총 토큰, 호출 횟수
        async with conn.execute(
            """SELECT
                   SUM(cost_usd) as total_cost,
                   SUM(total_tokens) as total_tokens,
                   COUNT(*) as call_count
               FROM usage
               WHERE created_at >= ? AND created_at <= ?""",
            (start_date.isoformat(), end_date.isoformat()),
        ) as cursor:
            row = await cursor.fetchone()
            total_cost = row["total_cost"] if row["total_cost"] is not None else 0.0
            total_tokens = row["total_tokens"] if row["total_tokens"] is not None else 0
            call_count = row["call_count"]

        # 모델별 비용
        by_model = await self.get_usage_by_model(start_date, end_date)

        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "call_count": call_count,
            "by_model": by_model,
        }

    async def close(self) -> None:
        """연결 종료"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._initialized = False
