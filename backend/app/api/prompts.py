from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.prompt import PromptTemplate, UserPrompt
from app.schemas.prompt import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    UserPromptCreate,
    UserPromptUpdate,
    UserPromptResponse,
)

router = APIRouter()


@router.get("/templates")
def list_templates(
    type: Optional[str] = None,
    position_type: Optional[str] = None,
    scenario_type: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(PromptTemplate)
    if type:
        q = q.filter(PromptTemplate.type == type)
    if position_type:
        q = q.filter(PromptTemplate.position_type == position_type)
    if scenario_type:
        q = q.filter(PromptTemplate.scenario_type == scenario_type)
    if status:
        q = q.filter(PromptTemplate.status == status)
    if keyword:
        q = q.filter(PromptTemplate.name.contains(keyword))
    total = q.count()
    items = q.order_by(PromptTemplate.updated_at.desc()).offset(skip).limit(limit).all()
    return {"items": [PromptTemplateResponse.model_validate(t).model_dump() for t in items], "total": total}


@router.post("/templates", response_model=PromptTemplateResponse, status_code=201)
def create_template(
    req: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    template = PromptTemplate(**req.model_dump(), created_by=current_user.id)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = (
        db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=PromptTemplateResponse)
def update_template(
    template_id: int,
    req: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    template = (
        db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    update_data = req.model_dump(exclude_unset=True)
    # If content changed, bump version
    if "content" in update_data and update_data["content"] != template.content:
        template.version += 1
    for k, v in update_data.items():
        setattr(template, k, v)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    template = (
        db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"status": "ok", "message": "模板已删除"}


@router.post("/templates/{template_id}/publish", response_model=PromptTemplateResponse)
def publish_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    template = (
        db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template.status = "published"
    db.commit()
    db.refresh(template)
    return template


@router.post("/templates/{template_id}/rollback", response_model=PromptTemplateResponse)
def rollback_template(
    template_id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    template = (
        db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if version >= template.version:
        raise HTTPException(
            status_code=400, detail="Cannot rollback to current or newer version"
        )
    template.version = version
    template.status = "draft"
    db.commit()
    db.refresh(template)
    return template


@router.post(
    "/templates/{template_id}/copy",
    response_model=PromptTemplateResponse,
    status_code=201,
)
def copy_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    template = (
        db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    new_template = PromptTemplate(
        name=f"{template.name} (副本)",
        type=template.type,
        position_type=template.position_type,
        scenario_type=template.scenario_type,
        content=template.content,
        variables_json=template.variables_json,
        input_file_requirements=template.input_file_requirements,
        output_format_requirements=template.output_format_requirements,
        processing_rules=template.processing_rules,
        exception_rules=template.exception_rules,
        example_input=template.example_input,
        example_output=template.example_output,
        version=1,
        status="draft",
        created_by=current_user.id,
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template


# User Prompts
@router.get("/user-prompts", response_model=List[UserPromptResponse])
def list_user_prompts(
    user_id: Optional[int] = None,
    scenario_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(UserPrompt)
    if user_id:
        q = q.filter(UserPrompt.user_id == user_id)
    if scenario_id:
        q = q.filter(UserPrompt.scenario_id == scenario_id)
    if status:
        q = q.filter(UserPrompt.status == status)
    return q.order_by(UserPrompt.updated_at.desc()).all()


@router.post("/user-prompts", response_model=UserPromptResponse, status_code=201)
def create_user_prompt(
    req: UserPromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    prompt = UserPrompt(**req.model_dump())
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.put("/user-prompts/{prompt_id}", response_model=UserPromptResponse)
def update_user_prompt(
    prompt_id: int,
    req: UserPromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    prompt = db.query(UserPrompt).filter(UserPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="User prompt not found")
    update_data = req.model_dump(exclude_unset=True)
    if "content" in update_data and update_data["content"] != prompt.content:
        prompt.version += 1
    for k, v in update_data.items():
        setattr(prompt, k, v)
    db.commit()
    db.refresh(prompt)
    return prompt
