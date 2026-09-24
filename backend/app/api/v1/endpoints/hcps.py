"""HCP endpoints."""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query  # <-- status is here
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.models.database import get_db
from app.models.user import User
from app.repositories.hcp_repository import HCPRepository
from app.repositories.audit_repository import AuditRepository
from app.services.hcp_service import HCPService
from app.services.audit_service import AuditService
from app.schemas.hcp import (
    HCPCreate,
    HCPUpdate,
    HCPResponse,
    HCPListResponse,
)
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


def get_hcp_service(
    db: AsyncSession = Depends(get_db),
) -> HCPService:
    """Dependency injection for HCP service."""
    hcp_repo = HCPRepository(db)
    return HCPService(hcp_repo)


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(AuditRepository(db))


@router.get("", response_model=HCPListResponse)
async def get_hcps(
    search: Optional[str] = Query(None, description="Search query"),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    service: HCPService = Depends(get_hcp_service),
) -> Dict[str, Any]:
    """Get all HCPs with filters and pagination."""
    try:
        filters = {
            "search": search,
            "specialty": specialty,
            "status": status_filter,
        }
        skip = (page - 1) * limit
        
        hcps = await service.get_hcps(filters, skip, limit)
        
        # Convert HCP objects to response models
        items = []
        for hcp in hcps:
            try:
                items.append(HCPResponse.model_validate(hcp))
            except Exception as e:
                logger.warning(f"Failed to validate HCP {hcp.id}: {e}")
                # Continue with next HCP instead of failing the whole request
                continue
        
        return {
            "items": items,
            "total": len(items),
            "page": page,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Get HCPs error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch HCPs: {str(e)}",
        )


@router.get("/{hcp_id}", response_model=HCPResponse)
async def get_hcp(
    hcp_id: str,
    current_user: User = Depends(get_current_user),
    service: HCPService = Depends(get_hcp_service),
) -> HCPResponse:
    """Get HCP by ID."""
    try:
        hcp = await service.get_hcp(hcp_id)
        return HCPResponse.model_validate(hcp)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Get HCP error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch HCP: {str(e)}",
        )


@router.post("", response_model=HCPResponse)
async def create_hcp(
    hcp_data: HCPCreate,
    current_user: User = Depends(get_current_user),
    service: HCPService = Depends(get_hcp_service),
    audit: AuditService = Depends(get_audit_service),
) -> HCPResponse:
    """Create a new HCP."""
    try:
        hcp = await service.create_hcp(hcp_data.model_dump())
        await audit.log(
            user_id=str(current_user.id),
            action="create",
            resource="hcp",
            resource_id=str(hcp.id),
            changes={"name": hcp_data.name, "specialty": hcp_data.specialty},
        )
        return HCPResponse.model_validate(hcp)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Create HCP error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create HCP: {str(e)}",
        )


@router.put("/{hcp_id}", response_model=HCPResponse)
async def update_hcp(
    hcp_id: str,
    hcp_data: HCPUpdate,
    current_user: User = Depends(get_current_user),
    service: HCPService = Depends(get_hcp_service),
    audit: AuditService = Depends(get_audit_service),
) -> HCPResponse:
    """Update an HCP."""
    try:
        changed_fields = hcp_data.model_dump(exclude_unset=True)
        hcp = await service.update_hcp(hcp_id, changed_fields)
        await audit.log(
            user_id=str(current_user.id),
            action="update",
            resource="hcp",
            resource_id=hcp_id,
            changes=changed_fields,
        )
        return HCPResponse.model_validate(hcp)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Update HCP error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update HCP: {str(e)}",
        )


@router.delete("/{hcp_id}")
async def delete_hcp(
    hcp_id: str,
    current_user: User = Depends(get_current_user),
    service: HCPService = Depends(get_hcp_service),
    audit: AuditService = Depends(get_audit_service),
) -> Dict[str, Any]:
    """Delete an HCP."""
    try:
        await service.delete_hcp(hcp_id)
        await audit.log(
            user_id=str(current_user.id),
            action="delete",
            resource="hcp",
            resource_id=hcp_id,
        )
        return {"success": True, "message": "HCP deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Delete HCP error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete HCP: {str(e)}",
        )