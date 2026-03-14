from datetime import date, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hr import EmployeeDocument, DocumentType
from app.models.alerts import AlarmRule, AlarmEvent, Notification
from app.models.core import User, Role


async def run_alert_check(db: AsyncSession) -> int:
    """
    Check all active EmployeeDocuments for upcoming expirations and create
    AlarmEvents + Notifications for users with the configured roles.
    Returns the number of new AlarmEvents created.
    """
    today = date.today()
    created_count = 0

    # Load all active documents with an end_date
    docs_result = await db.execute(
        select(EmployeeDocument).where(
            and_(
                EmployeeDocument.end_date.isnot(None),
                EmployeeDocument.status == "active",
            )
        )
    )
    documents = docs_result.scalars().all()

    for doc in documents:
        # Load alarm rules for this document type
        rules_result = await db.execute(
            select(AlarmRule).where(
                and_(
                    AlarmRule.document_type_id == doc.document_type_id,
                    AlarmRule.is_active.is_(True),
                )
            )
        )
        rules = rules_result.scalars().all()

        for rule in rules:
            threshold_date = doc.end_date - timedelta(days=rule.days_before)
            if today < threshold_date:
                # Not yet within the alert window
                continue

            # Check if an AlarmEvent already exists for this rule + document
            existing_result = await db.execute(
                select(AlarmEvent).where(
                    and_(
                        AlarmEvent.alarm_rule_id == rule.id,
                        AlarmEvent.employee_document_id == doc.id,
                    )
                )
            )
            if existing_result.scalar_one_or_none() is not None:
                continue  # already triggered

            # Create AlarmEvent
            event = AlarmEvent(
                alarm_rule_id=rule.id,
                employee_document_id=doc.id,
                status="sent",
            )
            db.add(event)
            await db.flush()
            created_count += 1

            # Notify users with the target roles
            notify_roles = rule.notify_roles or []
            if notify_roles:
                roles_result = await db.execute(
                    select(Role).where(Role.name.in_(notify_roles))
                )
                target_roles = roles_result.scalars().all()
                role_ids = [r.id for r in target_roles]

                users_result = await db.execute(
                    select(User).where(
                        and_(
                            User.role_id.in_(role_ids),
                            User.is_active.is_(True),
                        )
                    )
                )
                users = users_result.scalars().all()

                for user in users:
                    notif = Notification(
                        user_id=user.id,
                        title=f"Documento por vencer: {doc.id}",
                        body=(
                            f"El documento del empleado vence el {doc.end_date}. "
                            f"Quedan {(doc.end_date - today).days} días."
                        ),
                        link=f"/employees/{doc.employee_id}/documents/{doc.id}",
                    )
                    db.add(notif)

    await db.flush()
    return created_count
