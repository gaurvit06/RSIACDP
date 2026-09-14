from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignResponse


router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"]
)


@router.post(
    "/",
    response_model=CampaignResponse
)
def create_campaign(
    name: str,
    confidence: float = 0.0,
    status: str = "potential",
    db: Session = Depends(get_db)
):
    campaign = Campaign(
        name=name,
        confidence=confidence,
        status=status
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return campaign


@router.get(
    "/",
    response_model=list[CampaignResponse]
)
def get_campaigns(
    db: Session = Depends(get_db)
):
    return (
        db.query(Campaign)
        .order_by(Campaign.created_at.desc())
        .all()
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse
)
def get_campaign(
    campaign_id,
    db: Session = Depends(get_db)
):
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id)
        .first()
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found"
        )

    return campaign