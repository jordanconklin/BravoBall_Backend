from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import User, SavedFilter, SavedFilterCreate, SavedFilterUpdate, SavedFilterBase
from db import get_db
from auth import get_current_user

router = APIRouter()

# Create new filters
@router.post("/api/filters/", response_model=List[SavedFilterBase])
async def create_saved_filter(
    filters: SavedFilterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new saved filters for the current user"""
    try:
        created_filters = []
        for filter_data in filters.saved_filters:
            # Create new filter
            db_filter = SavedFilter(
                client_id=filter_data.id,
                user_id=current_user.id,
                name=filter_data.name,
                saved_time=filter_data.saved_time,
                saved_equipment=filter_data.saved_equipment,
                saved_training_style=filter_data.saved_training_style,
                saved_location=filter_data.saved_location,
                saved_difficulty=filter_data.saved_difficulty
            )
            db.add(db_filter)
            created_filters.append(db_filter)
        
        db.commit()
        return [format_filter_response(filter) for filter in created_filters]
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create saved filters: {str(e)}")



# format response definition
def format_filter_response(filter: SavedFilter) -> SavedFilterBase:
    return SavedFilterBase(
        id=str(filter.client_id),  # Ensure it's a string
        backend_id=filter.id,  # This is the integer backend ID
        name=filter.name,
        saved_time=filter.saved_time,
        saved_equipment=filter.saved_equipment,
        saved_training_style=filter.saved_training_style,
        saved_location=filter.saved_location,
        saved_difficulty=filter.saved_difficulty
    )

@router.get("/api/filters/", response_model=List[SavedFilterBase])
async def get_saved_filters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all saved filters for the current user"""
    filters = db.query(SavedFilter).filter(SavedFilter.user_id == current_user.id).all()
    return [format_filter_response(filter) for filter in filters]


@router.delete("/api/filters/{filter_id}")
async def delete_saved_filter(
    filter_id: int,  # Changed back to int
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a saved filter"""
    db_filter = db.query(SavedFilter).filter(
        SavedFilter.id == filter_id,
        SavedFilter.user_id == current_user.id
    ).first()
    
    if not db_filter:
        raise HTTPException(status_code=404, detail="Saved filter not found")
    
    db.delete(db_filter)
    db.commit()
    return {"message": "Filter deleted successfully"} 