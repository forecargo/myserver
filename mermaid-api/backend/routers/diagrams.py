from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Diagram, Project
from schemas import DiagramCreate, DiagramDetail, DiagramPatch, DiagramSummary

router = APIRouter(tags=["diagrams"])


@router.get("/projects/{project_id}/diagrams", response_model=list[DiagramSummary])
async def list_diagrams(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    result = await session.execute(
        select(Diagram)
        .where(Diagram.project_id == project_id)
        .order_by(Diagram.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/projects/{project_id}/diagrams",
    response_model=DiagramSummary,
    status_code=status.HTTP_201_CREATED,
)
async def create_diagram(
    project_id: int, body: DiagramCreate, session: AsyncSession = Depends(get_session)
):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    diagram = Diagram(project_id=project_id, name=body.name)
    session.add(diagram)
    await session.commit()
    await session.refresh(diagram)
    return diagram


@router.get("/diagrams/{diagram_id}", response_model=DiagramDetail)
async def get_diagram(diagram_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Diagram)
        .where(Diagram.id == diagram_id)
        .options(selectinload(Diagram.messages))
    )
    diagram = result.scalar_one_or_none()
    if not diagram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return diagram


@router.patch("/diagrams/{diagram_id}", response_model=DiagramDetail)
async def patch_diagram(
    diagram_id: int, body: DiagramPatch, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Diagram)
        .where(Diagram.id == diagram_id)
        .options(selectinload(Diagram.messages))
    )
    diagram = result.scalar_one_or_none()
    if not diagram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if body.name is not None:
        diagram.name = body.name
    if body.mermaid_code is not None:
        diagram.mermaid_code = body.mermaid_code
    await session.commit()
    await session.refresh(diagram)
    return diagram


@router.delete("/diagrams/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(diagram_id: int, session: AsyncSession = Depends(get_session)):
    diagram = await session.get(Diagram, diagram_id)
    if not diagram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await session.delete(diagram)
    await session.commit()
