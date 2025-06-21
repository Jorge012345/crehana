from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import (
    TaskListCreateDTO,
    TaskListUpdateDTO,
    TaskListResponseDTO,
)
from src.application.services import TaskListService
from src.domain.entities import User
from src.infrastructure.database import get_db_session
from src.presentation.dependencies import get_current_user, get_task_list_service

router = APIRouter(prefix="/task-lists", tags=["task-lists"])


@router.post("/", response_model=TaskListResponseDTO)
async def create_task_list(
    task_list_data: TaskListCreateDTO,
    current_user: User = Depends(get_current_user),
    task_list_service: TaskListService = Depends(get_task_list_service),
):
    """Crear una nueva lista de tareas"""
    task_list = await task_list_service.create_task_list(task_list_data, current_user.id)
    return task_list


@router.get("/", response_model=List[TaskListResponseDTO])
async def list_task_lists(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    task_list_service: TaskListService = Depends(get_task_list_service),
):
    """Listar todas las listas de tareas del usuario"""
    from src.application.dto import PaginationDTO
    pagination = PaginationDTO(skip=skip, limit=limit)
    task_lists = await task_list_service.list_user_task_lists(current_user.id, pagination)
    return task_lists


@router.get("/{task_list_id}", response_model=TaskListResponseDTO)
async def get_task_list(
    task_list_id: int,
    current_user: User = Depends(get_current_user),
    task_list_service: TaskListService = Depends(get_task_list_service),
):
    """Obtener una lista de tareas específica"""
    task_list = await task_list_service.get_task_list(task_list_id, current_user.id)
    return task_list


@router.put("/{task_list_id}", response_model=TaskListResponseDTO)
async def update_task_list(
    task_list_id: int,
    task_list_data: TaskListUpdateDTO,
    current_user: User = Depends(get_current_user),
    task_list_service: TaskListService = Depends(get_task_list_service),
):
    """Actualizar una lista de tareas"""
    task_list = await task_list_service.update_task_list(
        task_list_id, task_list_data, current_user.id
    )
    return task_list


@router.delete("/{task_list_id}")
async def delete_task_list(
    task_list_id: int,
    current_user: User = Depends(get_current_user),
    task_list_service: TaskListService = Depends(get_task_list_service),
):
    """Eliminar una lista de tareas"""
    success = await task_list_service.delete_task_list(task_list_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Lista de tareas no encontrada")
    return {"message": "Lista de tareas eliminada exitosamente"} 