# app/repositories/saml_auth_flow_repository.py
"""
SAML認証フローリポジトリ

saml_auth_flowテーブルへのデータアクセス層。
SELECT FOR UPDATEによる排他制御でチケット二重使用を防止。
"""

from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saml_auth_flow import SamlAuthFlow

logger = structlog.get_logger(__name__)


class SamlAuthFlowRepository:
    """SAML認証フロー状態のデータアクセス"""

    async def create_flow(
        self,
        db: AsyncSession,
        *,
        request_id: Optional[str],
        relay_nonce: str,
        sso_provider: str = "saml",
        redirect_uri: Optional[str] = None,
        relay_expires_at: Optional[datetime] = None,
    ) -> SamlAuthFlow:
        """AuthnRequest時にフローレコードを作成"""
        flow = SamlAuthFlow(
            request_id=request_id,
            relay_nonce=relay_nonce,
            sso_provider=sso_provider,
            redirect_uri=redirect_uri,
            relay_expires_at=relay_expires_at,
            status="authn_requested",
        )
        db.add(flow)
        await db.flush()
        logger.info(
            "SAML auth flow created",
            flow_id=flow.id,
        )
        return flow

    async def find_by_relay_nonce(
        self,
        db: AsyncSession,
        relay_nonce: str,
    ) -> Optional[SamlAuthFlow]:
        """relay_nonceでフローを検索"""
        stmt = select(SamlAuthFlow).where(
            SamlAuthFlow.relay_nonce == relay_nonce,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_to_acs_verified(
        self,
        db: AsyncSession,
        *,
        relay_nonce: str,
        user_id: int,
        subject_id: str,
        session_index: Optional[str],
        ticket_id: str,
        login_ticket_expires_at: datetime,
    ) -> Optional[SamlAuthFlow]:
        """ACS検証完了を記録（authn_requested → acs_verified）

        relay_nonceでフローを検索し、状態を更新する。
        """
        flow = await self.find_by_relay_nonce(db, relay_nonce)
        if not flow:
            logger.warning(
                "SAML auth flow not found for relay_nonce",
            )
            return None

        if flow.status != "authn_requested":
            logger.warning(
                "SAML auth flow in unexpected status for ACS",
                flow_id=flow.id,
                current_status=flow.status,
            )
            return None

        flow.mark_acs_verified(
            user_id=user_id,
            subject_id=subject_id,
            session_index=session_index,
            ticket_id=ticket_id,
            login_ticket_expires_at=login_ticket_expires_at,
        )
        await db.flush()
        logger.info(
            "SAML auth flow ACS verified",
            flow_id=flow.id,
        )
        return flow

    async def consume_ticket_exclusive(
        self,
        db: AsyncSession,
        ticket_id: str,
    ) -> Optional[SamlAuthFlow]:
        """チケットをDB排他ロック付きで消費（acs_verified → ticket_consumed）

        SELECT FOR UPDATE で行ロックを取得し、
        同一チケットの並行消費を防止する。

        Returns:
            SamlAuthFlow: 消費成功時のフローレコード
            None: チケットが見つからない/既に消費済みの場合
        """
        # SELECT ... FOR UPDATE で排他ロック
        stmt = (
            select(SamlAuthFlow)
            .where(SamlAuthFlow.ticket_id == ticket_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            logger.warning(
                "SAML auth flow not found for ticket",
            )
            return None

        if flow.status != "acs_verified":
            logger.warning(
                "SAML ticket already consumed or invalid status",
                flow_id=flow.id,
                current_status=flow.status,
            )
            return None

        flow.mark_ticket_consumed()
        await db.flush()
        logger.info(
            "SAML ticket consumed via DB exclusive lock",
            flow_id=flow.id,
        )
        return flow

    async def get_latest_session_index(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[str]:
        """ユーザーの最新session_indexを取得

        ticket_consumedフローから最新のsession_indexを返す。
        SLO LogoutRequest生成時にIdPへ送信するために使用。
        """
        stmt = (
            select(SamlAuthFlow.session_index)
            .where(
                SamlAuthFlow.user_id == user_id,
                SamlAuthFlow.session_index.isnot(None),
                SamlAuthFlow.status == "ticket_consumed",
            )
            .order_by(SamlAuthFlow.updated_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        session_index = result.scalar_one_or_none()
        if session_index:
            logger.debug(
                "Found session_index for user",
                user_id=user_id,
                session_index_present=True,
            )
        else:
            logger.debug("No session_index found for user", user_id=user_id)
        return session_index

    async def cleanup_expired_flows(
        self,
        db: AsyncSession,
    ) -> int:
        """期限切れフローのクリーンアップ

        定期実行（バッチ/タスク）で呼び出すことを想定。
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(SamlAuthFlow)
            .where(
                SamlAuthFlow.status.in_(["authn_requested", "acs_verified"]),
                SamlAuthFlow.login_ticket_expires_at.isnot(None),
                SamlAuthFlow.login_ticket_expires_at < now,
            )
            .values(status="expired", updated_at=now)
        )
        result = await db.execute(stmt)
        count = result.rowcount
        if count > 0:
            logger.info("Cleaned up expired SAML auth flows", count=count)
        return count
