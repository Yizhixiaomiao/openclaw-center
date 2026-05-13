from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User, BusinessScenario
from app.schemas.user import ScenarioCreate, ScenarioUpdate, ScenarioResponse

router = APIRouter()


@router.get("")
def list_scenarios(
    user_id: int = None,
    status: str = None,
    scenario_type: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(BusinessScenario)
    if user_id:
        q = q.filter(BusinessScenario.user_id == user_id)
    if status:
        q = q.filter(BusinessScenario.status == status)
    if scenario_type:
        q = q.filter(BusinessScenario.scenario_type == scenario_type)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return {"items": [ScenarioResponse.model_validate(s).model_dump() for s in items], "total": total}


@router.post("", response_model=ScenarioResponse, status_code=201)
def create_scenario(req: ScenarioCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "support"))):
    scenario = BusinessScenario(**req.model_dump())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scenario = db.query(BusinessScenario).filter(BusinessScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(scenario_id: int, req: ScenarioUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "support"))):
    scenario = db.query(BusinessScenario).filter(BusinessScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(scenario, k, v)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    scenario = db.query(BusinessScenario).filter(BusinessScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(scenario)
    db.commit()
