from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.base import BaseRepository
from app.infrastructure.repositories.models import Alert, AlertTriage, FlowHistory


class PredictionRepository(BaseRepository[FlowHistory]):
    """
    Repository managing FlowHistory records and Intrusion Alerts.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(FlowHistory, session)

    async def create_flow(
        self,
        raw_41_features: Dict[str, Any],
        predicted_category: str,
        confidence_score: float,
        inference_latency_ms: float,
        source_ip: Optional[str] = None,
        source_port: Optional[int] = None,
        destination_ip: Optional[str] = None,
        destination_port: Optional[int] = None,
        protocol_type: Optional[str] = None,
        model_id: Optional[uuid.UUID] = None,
    ) -> FlowHistory:
        """Record classified network flow statistical vector."""
        flow = FlowHistory(
            raw_41_features=raw_41_features,
            predicted_category=predicted_category,
            confidence_score=confidence_score,
            inference_latency_ms=inference_latency_ms,
            source_ip=source_ip,
            source_port=source_port,
            destination_ip=destination_ip,
            destination_port=destination_port,
            protocol_type=protocol_type,
            model_id=model_id,
        )
        self.session.add(flow)
        await self.session.flush()
        await self.session.refresh(flow)
        return flow

    async def create_alert(
        self,
        flow_id: int,
        attack_category: str,
        severity_level: str,
        shap_attributions: Optional[Dict[str, Any]] = None,
        status: str = "NEW",
    ) -> Alert:
        """Create threat alert record associated with a flow."""
        alert = Alert(
            flow_id=flow_id,
            attack_category=attack_category,
            severity_level=severity_level,
            shap_attributions=shap_attributions,
            status=status,
        )
        self.session.add(alert)
        await self.session.flush()
        await self.session.refresh(alert)
        return alert

    async def get_alert_by_id(self, alert_id: uuid.UUID) -> Optional[Alert]:
        """Fetch alert by unique UUID."""
        result = await self.session.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def list_alerts(
        self,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status_val: Optional[str] = None,
    ) -> List[Alert]:
        """Fetch paginated, filtered threat alerts."""
        query = select(Alert)
        if category:
            query = query.where(Alert.attack_category == category)
        if severity:
            query = query.where(Alert.severity_level == severity)
        if status_val:
            query = query.where(Alert.status == status_val)

        query = query.order_by(Alert.alert_timestamp.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_triage_entry(
        self,
        alert: Alert,
        analyst_user_id: Optional[uuid.UUID],
        new_status: str,
        notes: Optional[str] = None,
    ) -> AlertTriage:
        """Record analyst alert triage state transition."""
        triage = AlertTriage(
            alert_id=alert.id,
            analyst_user_id=analyst_user_id,
            previous_status=alert.status,
            new_status=new_status,
            notes=notes,
        )
        alert.status = new_status
        self.session.add(triage)
        await self.session.flush()
        await self.session.refresh(triage)
        return triage
