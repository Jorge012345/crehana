from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto import (
    TaskCreateDTO,
    TaskUpdateDTO,
    TaskResponseDTO,
    TaskListResponseDTO,
)
from src.application.services import TaskService
from src.domain.entities import User, TaskStatus, TaskPriority
from src.infrastructure.database import get_db_session
from src.presentation.dependencies import get_current_user, get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponseDTO)
async def create_task(
    task_data: TaskCreateDTO,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """Crear una nueva tarea"""
    task = await task_service.create_task(task_data.task_list_id, task_data, current_user.id)
    return task


@router.get("/", response_model=List[TaskResponseDTO])
async def list_tasks(
    task_list_id: int = Query(..., description="ID de la lista de tareas"),
    status: Optional[TaskStatus] = Query(None, description="Filtrar por estado"),
    priority: Optional[TaskPriority] = Query(None, description="Filtrar por prioridad"),
    assigned_to: Optional[int] = Query(None, description="Filtrar por usuario asignado"),
    overdue_only: bool = Query(False, description="Solo tareas vencidas"),
    skip: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(100, description="Número máximo de registros"),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """Listar tareas con filtros opcionales"""
    from src.application.dto import TaskFilterDTO, PaginationDTO
    
    filters = TaskFilterDTO(
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        overdue_only=overdue_only,
    )
    pagination = PaginationDTO(skip=skip, limit=limit)
    
    tasks = await task_service.list_tasks(
        task_list_id=task_list_id,
        filters=filters,
        pagination=pagination,
        user_id=current_user.id,
    )
    return tasks


@router.get("/{task_id}", response_model=TaskResponseDTO)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """Obtener una tarea específica"""
    task = await task_service.get_task(task_id, current_user.id)
    return task


@router.put("/{task_id}", response_model=TaskResponseDTO)
async def update_task(
    task_id: int,
    task_data: TaskUpdateDTO,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """Actualizar una tarea"""
    task = await task_service.update_task(task_id, task_data, current_user.id)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """Eliminar una tarea"""
    success = await task_service.delete_task(task_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"message": "Tarea eliminada exitosamente"}


@router.patch("/{task_id}/status", response_model=TaskResponseDTO)
async def update_task_status(
    task_id: int,
    status: TaskStatus,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """Actualizar solo el estado de una tarea"""
    from src.application.dto import TaskStatusUpdateDTO
    
    status_data = TaskStatusUpdateDTO(status=status)
    task = await task_service.update_task_status(task_id, status_data, current_user.id)
    return task


@router.post("/{task_id}/assign/{user_id}", response_model=TaskResponseDTO)
async def assign_task(
    task_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """Asignar una tarea a un usuario"""
    from src.application.dto import TaskUpdateDTO
    
    # Use update_task to assign the task
    update_data = TaskUpdateDTO(assigned_to=user_id)
    task = await task_service.update_task(task_id, update_data, current_user.id)
    return task 