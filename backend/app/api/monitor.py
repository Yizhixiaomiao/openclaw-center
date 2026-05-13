from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from app.utils.deps import get_db, get_current_user
from app.models.user import User
from app.models.machine import Machine
from app.models.log import AgentLog
from app.models.plan import CodingPlan

router = APIRouter()


@router.get("/machines")
def monitor_machines(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Machine)
    if status:
        q = q.filter(Machine.status == status)
    machines = q.all()
    # Mark machines offline if no heartbeat for 3 minutes
    threshold = datetime.now() - timedelta(minutes=3)
    result = []
    for m in machines:
        is_online = m.last_heartbeat_at and m.last_heartbeat_at > threshold
        result.append(
            {
                "id": m.id,
                "code": m.code,
                "hostname": m.hostname,
                "ip": m.ip,
                "status": m.status,
                "is_online": is_online,
                "user_id": m.user_id,
                "department": m.department,
                "cpu_usage": m.cpu_usage,
                "memory_usage": m.memory_usage,
                "disk_usage": m.disk_usage,
                "last_heartbeat_at": str(m.last_heartbeat_at)
                if m.last_heartbeat_at
                else None,
            }
        )
    return result


@router.get("/overview")
def monitor_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_machines = db.query(Machine).count()
    threshold = datetime.now() - timedelta(minutes=3)
    online_machines = (
        db.query(Machine).filter(Machine.last_heartbeat_at > threshold).count()
    )
    total_users = db.query(User).filter(User.status == "active").count()
    error_machines = db.query(Machine).filter(Machine.status == "error").count()
    # Check plans at risk
    plans = db.query(CodingPlan).filter(CodingPlan.status == "active").all()
    warning_plans = [
        p
        for p in plans
        if p.quota_limit
        and p.quota_used
        and (p.quota_used / p.quota_limit * 100) >= float(p.warning_threshold)
    ]
    return {
        "total_machines": total_machines,
        "online_machines": online_machines,
        "offline_machines": total_machines - online_machines,
        "error_machines": error_machines,
        "total_users": total_users,
        "warning_plans": len(warning_plans),
    }


@router.get("/logs")
def monitor_logs(
    machine_id: Optional[int] = None,
    level: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AgentLog)
    if machine_id:
        q = q.filter(AgentLog.machine_id == machine_id)
    if level:
        q = q.filter(AgentLog.level == level)
    if category:
        q = q.filter(AgentLog.category == category)
    total = q.count()
    logs = q.order_by(AgentLog.created_at.desc()).offset(skip).limit(limit).all()

    # Enrich logs with machine info
    machine_ids = list({log.machine_id for log in logs})
    machines = db.query(Machine).filter(Machine.id.in_(machine_ids)).all() if machine_ids else []
    machine_map = {m.id: m for m in machines}

    items = []
    for log in logs:
        m = machine_map.get(log.machine_id)
        items.append({
            "id": log.id,
            "machine_id": log.machine_id,
            "machine_code": m.code if m else None,
            "hostname": m.hostname if m else None,
            "ip": m.ip if m else None,
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "created_at": str(log.created_at),
        })
    return {"items": items, "total": total}


@router.get("/alerts")
def monitor_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alerts = []
    # Offline machines
    threshold = datetime.now() - timedelta(minutes=3)
    offline = (
        db.query(Machine)
        .filter(Machine.status != "disabled", Machine.last_heartbeat_at < threshold)
        .all()
    )
    for m in offline:
        alerts.append(
            {
                "type": "offline",
                "machine_id": m.id,
                "machine_code": m.code,
                "hostname": m.hostname,
                "ip": m.ip,
                "message": f"Machine {m.hostname or m.code} offline",
            }
        )
    # Error machines
    error_machines = db.query(Machine).filter(Machine.status == "error").all()
    for m in error_machines:
        alerts.append(
            {
                "type": "error",
                "machine_id": m.id,
                "machine_code": m.code,
                "hostname": m.hostname,
                "ip": m.ip,
                "message": f"Machine {m.hostname or m.code} in error state",
            }
        )
    # Plan warnings
    plans = db.query(CodingPlan).filter(CodingPlan.status == "active").all()
    for p in plans:
        if p.quota_limit and p.quota_used:
            pct = p.quota_used / p.quota_limit * 100
            if pct >= 100:
                alerts.append(
                    {
                        "type": "plan_high_risk",
                        "plan_id": p.id,
                        "message": f"Plan {p.plan_name} quota exceeded ({pct:.1f}%)",
                    }
                )
            elif pct >= float(p.warning_threshold):
                alerts.append(
                    {
                        "type": "plan_warning",
                        "plan_id": p.id,
                        "message": f"Plan {p.plan_name} usage at {pct:.1f}%",
                    }
                )
    return alerts
