"""Alert API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from typing import Optional
import logging

from app.database import get_db
from app import models, schemas

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/alerts", response_model=schemas.AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    criticality: Optional[str] = Query(None, description="Filter by criticality (High, Medium, Low)"),
    show_irrelevant: bool = Query(False, description="Show alerts marked as irrelevant"),
    db: Session = Depends(get_db)
):
    """
    List all alerts with pagination and filtering.
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 50, max: 100)
    - **criticality**: Filter by criticality level
    - **show_irrelevant**: Include alerts marked as not relevant (default: false)
    """
    try:
        # Base query with relationships
        query = db.query(models.Alert).options(
            joinedload(models.Alert.classifications),
            joinedload(models.Alert.user_actions)
        )
        
        # Filter out irrelevant alerts unless explicitly requested
        if not show_irrelevant:
            # Subquery to find alert IDs with 'irrelevant' action
            irrelevant_alert_ids = db.query(models.UserAction.alert_id).filter(
                models.UserAction.action == "irrelevant"
            ).subquery()
            
            query = query.filter(~models.Alert.id.in_(irrelevant_alert_ids))
        
        # Filter by criticality if specified
        if criticality:
            # Get alert IDs with matching criticality
            alert_ids_with_criticality = db.query(models.Classification.alert_id).filter(
                models.Classification.criticality == criticality
            ).distinct().subquery()
            
            query = query.filter(models.Alert.id.in_(alert_ids_with_criticality))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and sorting
        offset = (page - 1) * limit
        alerts = query.order_by(desc(models.Alert.effective_at)).offset(offset).limit(limit).all()
        
        # Build response with latest classification for each alert
        alert_responses = []
        for alert in alerts:
            alert_dict = {
                "id": alert.id,
                "natural_key": alert.natural_key,
                "source": alert.source,
                "provider_id": alert.provider_id,
                "title": alert.title,
                "summary": alert.summary,
                "event_type": alert.event_type,
                "severity": alert.severity,
                "urgency": alert.urgency,
                "area": alert.area,
                "effective_at": alert.effective_at,
                "expires_at": alert.expires_at,
                "url": alert.url,
                "created_at": alert.created_at,
                "latitude": alert.latitude,
                "longitude": alert.longitude,
                "latest_classification": None,
                "user_actions": []
            }
            
            # Get latest classification
            if alert.classifications:
                latest_class = max(alert.classifications, key=lambda c: c.created_at)
                alert_dict["latest_classification"] = {
                    "id": latest_class.id,
                    "alert_id": latest_class.alert_id,
                    "criticality": latest_class.criticality,
                    "rationale": latest_class.rationale,
                    "model_version": latest_class.model_version,
                    "created_at": latest_class.created_at
                }
            
            # Include user actions
            alert_dict["user_actions"] = [
                {
                    "id": action.id,
                    "alert_id": action.alert_id,
                    "action": action.action,
                    "note": action.note,
                    "actor": action.actor,
                    "created_at": action.created_at
                }
                for action in alert.user_actions
            ]
            
            alert_responses.append(alert_dict)
        
        has_more = (offset + limit) < total
        
        return schemas.AlertListResponse(
            alerts=alert_responses,
            total=total,
            page=page,
            limit=limit,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error listing alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/alerts/{alert_id}", response_model=schemas.AlertDetailResponse)
async def get_alert_detail(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific alert.
    
    Includes raw payload and full classification/action history.
    """
    try:
        alert = db.query(models.Alert).options(
            joinedload(models.Alert.classifications),
            joinedload(models.Alert.user_actions)
        ).filter(models.Alert.id == alert_id).first()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Build detailed response
        response = {
            "id": alert.id,
            "natural_key": alert.natural_key,
            "source": alert.source,
            "provider_id": alert.provider_id,
            "title": alert.title,
            "summary": alert.summary,
            "event_type": alert.event_type,
            "severity": alert.severity,
            "urgency": alert.urgency,
            "area": alert.area,
            "effective_at": alert.effective_at,
            "expires_at": alert.expires_at,
            "url": alert.url,
            "created_at": alert.created_at,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "raw_payload": alert.raw_payload,
            "latest_classification": None,
            "user_actions": []
        }
        
        # Get latest classification
        if alert.classifications:
            latest_class = max(alert.classifications, key=lambda c: c.created_at)
            response["latest_classification"] = {
                "id": latest_class.id,
                "alert_id": latest_class.alert_id,
                "criticality": latest_class.criticality,
                "rationale": latest_class.rationale,
                "model_version": latest_class.model_version,
                "created_at": latest_class.created_at
            }
        
        # Include user actions
        response["user_actions"] = [
            {
                "id": action.id,
                "alert_id": action.alert_id,
                "action": action.action,
                "note": action.note,
                "actor": action.actor,
                "created_at": action.created_at
            }
            for action in alert.user_actions
        ]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve alert details")


@router.post("/alerts/{alert_id}/not-relevant")
async def mark_not_relevant(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark an alert as not relevant.
    This will move it to the bottom of the list by default.
    """
    try:
        # Check if alert exists
        alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Check if already marked as irrelevant
        existing_action = db.query(models.UserAction).filter(
            and_(
                models.UserAction.alert_id == alert_id,
                models.UserAction.action == "irrelevant"
            )
        ).first()
        
        if existing_action:
            return {"message": "Alert already marked as not relevant", "action_id": existing_action.id}
        
        # Create user action
        user_action = models.UserAction(
            alert_id=alert_id,
            action="irrelevant",
            note=None,
            actor=None  # TODO: Add actor when auth is implemented
        )
        
        db.add(user_action)
        db.commit()
        db.refresh(user_action)
        
        logger.info(f"Alert {alert_id} marked as not relevant")
        
        return {
            "message": "Alert marked as not relevant",
            "action_id": user_action.id,
            "alert_id": alert_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alert as not relevant: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to mark alert as not relevant")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    action_data: schemas.UserActionCreate,
    db: Session = Depends(get_db)
):
    """
    Acknowledge an alert with optional note.
    """
    try:
        # Check if alert exists
        alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Check if already acknowledged
        existing_action = db.query(models.UserAction).filter(
            and_(
                models.UserAction.alert_id == alert_id,
                models.UserAction.action == "acknowledged"
            )
        ).first()
        
        if existing_action:
            return {"message": "Alert already acknowledged", "action_id": existing_action.id}
        
        # Create user action
        user_action = models.UserAction(
            alert_id=alert_id,
            action="acknowledged",
            note=action_data.note,
            actor=None  # TODO: Add actor when auth is implemented
        )
        
        db.add(user_action)
        db.commit()
        db.refresh(user_action)
        
        logger.info(f"Alert {alert_id} acknowledged")
        
        return {
            "message": "Alert acknowledged",
            "action_id": user_action.id,
            "alert_id": alert_id,
            "note": user_action.note
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

