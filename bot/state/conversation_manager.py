"""会話履歴管理

チャンネルごとのペルソナ設定と会話履歴を管理します。
"""

import logging
from collections import defaultdict
from typing import Optional

from bot.config import get_settings
from bot.models import ConversationMessage, ChannelState

logger = logging.getLogger(__name__)


class ConversationManager:
    """会話履歴マネージャー

    チャンネルごとにペルソナIDと会話履歴を管理します。
    """

    def __init__(self) -> None:
        """初期化"""
        self.settings = get_settings()

        # チャンネルID -> ペルソナID
        self._channel_personas: dict[int, str] = {}

        # チャンネルID -> 会話履歴
        self._conversation_history: dict[int, list[ConversationMessage]] = defaultdict(list)

        logger.info("ConversationManager initialized")

    def set_persona(self, channel_id: int, persona_id: str) -> None:
        """チャンネルのペルソナを設定

        Args:
            channel_id: チャンネルID
            persona_id: ペルソナID
        """
        self._channel_personas[channel_id] = persona_id
        logger.info(
            "Persona set for channel",
            extra={"channel_id": channel_id, "persona_id": persona_id}
        )

    def get_persona(self, channel_id: int) -> Optional[str]:
        """チャンネルのペルソナを取得

        Args:
            channel_id: チャンネルID

        Returns:
            ペルソナID（未設定の場合はNone）
        """
        return self._channel_personas.get(channel_id)

    def add_message(
        self,
        channel_id: int,
        role: str,
        content: str
    ) -> None:
        """会話履歴にメッセージを追加

        Args:
            channel_id: チャンネルID
            role: メッセージの役割（"user" or "assistant"）
            content: メッセージ内容
        """
        message: ConversationMessage = {
            "role": role,
            "content": content
        }

        history = self._conversation_history[channel_id]
        history.append(message)

        # 履歴の上限を超えたら古いものを削除
        if len(history) > self.settings.conversation_history_limit:
            removed_count = len(history) - self.settings.conversation_history_limit
            self._conversation_history[channel_id] = history[removed_count:]
            logger.debug(
                f"Trimmed conversation history",
                extra={
                    "channel_id": channel_id,
                    "removed_count": removed_count,
                    "new_length": len(self._conversation_history[channel_id])
                }
            )

        logger.debug(
            "Message added to conversation history",
            extra={
                "channel_id": channel_id,
                "role": role,
                "content_length": len(content),
                "history_length": len(self._conversation_history[channel_id])
            }
        )

    def get_history(
        self,
        channel_id: int,
        limit: Optional[int] = None
    ) -> list[ConversationMessage]:
        """会話履歴を取得

        Args:
            channel_id: チャンネルID
            limit: 取得する最大メッセージ数（Noneの場合は設定値を使用）

        Returns:
            会話履歴（新しい順）
        """
        history = self._conversation_history[channel_id]

        if limit is None:
            limit = self.settings.conversation_context_window

        # 最新のN件を返す
        result = history[-limit:] if limit > 0 else history

        logger.debug(
            "Retrieved conversation history",
            extra={
                "channel_id": channel_id,
                "requested_limit": limit,
                "returned_count": len(result),
                "total_history": len(history)
            }
        )

        return result

    def clear_history(self, channel_id: int) -> None:
        """会話履歴をクリア

        Args:
            channel_id: チャンネルID
        """
        if channel_id in self._conversation_history:
            history_length = len(self._conversation_history[channel_id])
            del self._conversation_history[channel_id]
            logger.info(
                "Conversation history cleared",
                extra={"channel_id": channel_id, "cleared_count": history_length}
            )

    def reset_persona(self, channel_id: int) -> None:
        """ペルソナを解除

        Args:
            channel_id: チャンネルID
        """
        if channel_id in self._channel_personas:
            old_persona_id = self._channel_personas[channel_id]
            del self._channel_personas[channel_id]
            logger.info(
                "Persona reset",
                extra={"channel_id": channel_id, "old_persona_id": old_persona_id}
            )

        # 会話履歴もクリア
        self.clear_history(channel_id)

    def get_channel_state(self, channel_id: int) -> ChannelState:
        """チャンネルの完全な状態を取得

        Args:
            channel_id: チャンネルID

        Returns:
            チャンネル状態
        """
        return ChannelState(
            persona_id=self.get_persona(channel_id) or "",
            history=self.get_history(channel_id)
        )

    def get_all_channels(self) -> list[int]:
        """全チャンネルIDを取得

        Returns:
            チャンネルIDのリスト
        """
        # ペルソナ設定または会話履歴があるチャンネル
        channel_ids = set(self._channel_personas.keys()) | set(self._conversation_history.keys())
        return list(channel_ids)

    def get_stats(self) -> dict[str, int]:
        """統計情報を取得

        Returns:
            統計情報
        """
        total_messages = sum(len(history) for history in self._conversation_history.values())

        return {
            "total_channels": len(self.get_all_channels()),
            "channels_with_persona": len(self._channel_personas),
            "channels_with_history": len(self._conversation_history),
            "total_messages": total_messages,
        }
