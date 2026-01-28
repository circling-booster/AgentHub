"""SQLite Conversation Storage Adapter

aiosqlite 기반 비동기 SQLite 저장소입니다.
WAL 모드와 쓰기 Lock을 사용하여 동시성을 처리합니다.
"""

import asyncio
import json
from datetime import datetime

import aiosqlite

from src.domain.entities.conversation import Conversation
from src.domain.entities.enums import MessageRole
from src.domain.entities.message import Message
from src.domain.entities.tool_call import ToolCall
from src.domain.ports.outbound.storage_port import ConversationStoragePort


class SqliteConversationStorage(ConversationStoragePort):
    """
    SQLite 기반 대화 저장소

    Features:
    - WAL 모드: 읽기와 쓰기가 서로 차단하지 않음
    - 싱글톤 연결: 연결 오버헤드 최소화
    - 쓰기 Lock: 쓰기 작업 직렬화 (database is locked 방지)
    - busy_timeout: Lock 대기 시간 설정

    Attributes:
        _db_path: 데이터베이스 파일 경로
        _connection: aiosqlite 연결
        _write_lock: 쓰기 직렬화를 위한 Lock
        _initialized: 초기화 완료 여부
    """

    def __init__(self, db_path: str) -> None:
        """
        Args:
            db_path: SQLite 데이터베이스 파일 경로
        """
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """
        데이터베이스 초기화

        WAL 모드를 활성화하고 테이블을 생성합니다.
        """
        if self._initialized:
            return

        conn = await self._get_connection()

        # WAL 모드 활성화 (동시 읽기/쓰기 지원)
        await conn.execute("PRAGMA journal_mode=WAL")

        # busy_timeout 설정 (5초 대기)
        await conn.execute("PRAGMA busy_timeout=5000")

        # Foreign Key 활성화
        await conn.execute("PRAGMA foreign_keys=ON")

        # 테이블 생성
        await conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id);

            CREATE TABLE IF NOT EXISTS tool_calls (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                arguments JSON,
                result JSON,
                error TEXT,
                duration_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_tool_calls_message
            ON tool_calls(message_id);
            """
        )

        await conn.commit()
        self._initialized = True

    async def _get_connection(self) -> aiosqlite.Connection:
        """싱글톤 연결 반환"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self._db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def save_conversation(self, conversation: Conversation) -> None:
        """대화 저장/갱신"""
        async with self._write_lock:
            conn = await self._get_connection()
            await conn.execute(
                """
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    updated_at = excluded.updated_at
                """,
                (
                    conversation.id,
                    conversation.title,
                    conversation.created_at.isoformat(),
                    conversation.updated_at.isoformat(),
                ),
            )
            await conn.commit()

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """대화 조회"""
        conn = await self._get_connection()
        async with conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None

            return Conversation(
                id=row["id"],
                title=row["title"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        """대화 목록 조회 (최신순)"""
        conn = await self._get_connection()
        async with conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                Conversation(
                    id=row["id"],
                    title=row["title"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]

    async def delete_conversation(self, conversation_id: str) -> bool:
        """대화 삭제 (Cascade로 메시지, tool_calls도 삭제)"""
        async with self._write_lock:
            conn = await self._get_connection()
            cursor = await conn.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            await conn.commit()
            return cursor.rowcount > 0

    async def save_message(self, message: Message) -> None:
        """메시지 저장"""
        async with self._write_lock:
            conn = await self._get_connection()
            await conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    content = excluded.content
                """,
                (
                    message.id,
                    message.conversation_id,
                    message.role.value,
                    message.content,
                    message.created_at.isoformat(),
                ),
            )

            # Tool calls 저장 (있는 경우)
            for tool_call in message.tool_calls:
                await conn.execute(
                    """
                    INSERT INTO tool_calls (
                        id, message_id, tool_name, arguments,
                        result, error, duration_ms, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO NOTHING
                    """,
                    (
                        tool_call.id,
                        message.id,
                        tool_call.tool_name,
                        json.dumps(tool_call.arguments),
                        json.dumps(tool_call.result) if tool_call.result else None,
                        tool_call.error,
                        tool_call.duration_ms,
                        tool_call.created_at.isoformat(),
                    ),
                )

            await conn.commit()

    async def get_messages(
        self,
        conversation_id: str,
        limit: int | None = None,
    ) -> list[Message]:
        """대화의 메시지 조회 (시간순)"""
        conn = await self._get_connection()

        # limit이 있으면 최근 N개, 없으면 전체
        # rowid로 보조 정렬하여 동일 타임스탬프에서도 삽입 순서 보장
        if limit:
            query = """
                SELECT id, conversation_id, role, content, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
            """
            params = (conversation_id, limit)
        else:
            query = """
                SELECT id, conversation_id, role, content, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at, rowid
            """
            params = (conversation_id,)

        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        # limit이 있는 경우 결과를 시간순으로 정렬
        if limit:
            rows = list(reversed(rows))

        messages = []
        for row in rows:
            message = Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=MessageRole(row["role"]),
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

            # Tool calls 로드
            async with conn.execute(
                """
                SELECT id, tool_name, arguments, result, error, duration_ms, created_at
                FROM tool_calls
                WHERE message_id = ?
                ORDER BY created_at
                """,
                (message.id,),
            ) as tc_cursor:
                tc_rows = await tc_cursor.fetchall()
                for tc_row in tc_rows:
                    tool_call = ToolCall(
                        id=tc_row["id"],
                        tool_name=tc_row["tool_name"],
                        arguments=json.loads(tc_row["arguments"]) if tc_row["arguments"] else {},
                        result=json.loads(tc_row["result"]) if tc_row["result"] else None,
                        error=tc_row["error"],
                        duration_ms=tc_row["duration_ms"],
                        created_at=datetime.fromisoformat(tc_row["created_at"]),
                    )
                    message.tool_calls.append(tool_call)

            messages.append(message)

        return messages

    async def close(self) -> None:
        """연결 종료"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._initialized = False
