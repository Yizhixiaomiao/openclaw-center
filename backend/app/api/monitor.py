from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from typing import Optional, List
from datetime import datetime, timedelta
from app.utils.deps import get_db, get_current_user
from app.models.user import User
from app.models.machine import Machine
from app.models.log import AgentLog
from app.models.plan import CodingPlan, UsageRecord
from app.models.skill import MachineSkill, Skill
from app.models.deploy import DeployTaskItem

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


@router.get("/usage-trend")
def usage_trend(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily API usage trend (calls + tokens) for the last N days."""
    start_date = datetime.now() - timedelta(days=days)
    rows = (
        db.query(
            sa_func.date(UsageRecord.occurred_at).label("date"),
            sa_func.sum(UsageRecord.calls).label("total_calls"),
            sa_func.sum(UsageRecord.tokens).label("total_tokens"),
        )
        .filter(UsageRecord.occurred_at >= start_date)
        .group_by(sa_func.date(UsageRecord.occurred_at))
        .order_by(sa_func.date(UsageRecord.occurred_at))
        .all()
    )

    # Build a date-keyed map, then fill gaps with 0
    data_map = {}
    for r in rows:
        date_str = str(r.date)
        data_map[date_str] = {
            "date": date_str,
            "total_calls": r.total_calls or 0,
            "total_tokens": r.total_tokens or 0,
        }

    result = []
    for i in range(days):
        d = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        if d in data_map:
            result.append(data_map[d])
        else:
            result.append({"date": d, "total_calls": 0, "total_tokens": 0})

    return result


@router.get("/machine-stats")
def machine_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Machine distribution by status and department."""
    threshold = datetime.now() - timedelta(minutes=3)
    machines = db.query(Machine).all()

    # Status distribution — use heartbeat to determine actual online/offline
    status_map = {"online": 0, "offline": 0, "error": 0, "pending_init": 0, "disabled": 0}
    dept_map = {}

    for m in machines:
        # Determine actual online status
        is_online = m.last_heartbeat_at and m.last_heartbeat_at > threshold
        if m.status == "error":
            status_map["error"] += 1
        elif m.status == "disabled":
            status_map["disabled"] += 1
        elif m.status == "pending_init":
            status_map["pending_init"] += 1
        elif is_online:
            status_map["online"] += 1
        else:
            status_map["offline"] += 1

        # Department distribution
        dept = m.department or "未分配"
        dept_map[dept] = dept_map.get(dept, 0) + 1

    status_distribution = [
        {"name": "在线", "value": status_map["online"]},
        {"name": "离线", "value": status_map["offline"]},
        {"name": "异常", "value": status_map["error"]},
        {"name": "待初始化", "value": status_map["pending_init"]},
        {"name": "已禁用", "value": status_map["disabled"]},
    ]
    # Filter out zero values
    status_distribution = [s for s in status_distribution if s["value"] > 0]

    department_distribution = [
        {"name": k, "value": v} for k, v in sorted(dept_map.items(), key=lambda x: -x[1])
    ]

    return {
        "status_distribution": status_distribution,
        "department_distribution": department_distribution,
    }


@router.get("/skill-ranking")
def skill_ranking(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top N most-installed skills."""
    rows = (
        db.query(
            Skill.name,
            sa_func.count(MachineSkill.id).label("install_count"),
        )
        .join(Skill, MachineSkill.skill_id == Skill.id)
        .filter(MachineSkill.status != "removed")
        .group_by(MachineSkill.skill_id)
        .order_by(sa_func.count(MachineSkill.id).desc())
        .limit(limit)
        .all()
    )
    return [{"name": r.name or "未知", "install_count": r.install_count} for r in rows]


@router.get("/deploy-stats")
def deploy_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deploy task item status distribution."""
    rows = (
        db.query(
            DeployTaskItem.status,
            sa_func.count(DeployTaskItem.id).label("count"),
        )
        .group_by(DeployTaskItem.status)
        .all()
    )
    label_map = {
        "pending": "待执行",
        "in_progress": "执行中",
        "completed": "已完成",
        "failed": "失败",
        "partial": "部分完成",
    }
    result = []
    for r in rows:
        result.append({"name": label_map.get(r.status, r.status), "value": r.count})
    return result


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
                "message": f"机器 {m.hostname or m.code} 离线",
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
                "message": f"机器 {m.hostname or m.code} 处于异常状态",
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
                        "message": f"套餐 {p.plan_name} 额度已超限 ({pct:.1f}%)",
                    }
                )
            elif pct >= float(p.warning_threshold):
                alerts.append(
                    {
                        "type": "plan_warning",
                        "plan_id": p.id,
                        "message": f"套餐 {p.plan_name} 使用率 {pct:.1f}%",
                    }
                )
    return alerts
