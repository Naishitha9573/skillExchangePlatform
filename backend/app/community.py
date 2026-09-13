"""Public discovery data. Deliberately excludes account and conversation details."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Rating, Skill, User

router = APIRouter(prefix="/api/v1/community", tags=["Community"])


def member_json(user, rating=0, reviews=0):
    return {
        "id": user.id, "full_name": user.full_name, "bio": user.bio,
        "location": user.location, "avatar_url": user.avatar_url,
        "rating": round(rating or 0, 1), "review_count": reviews,
        "skills": [{"id": s.id, "title": s.title, "type": s.type, "category": s.category,
                    "level": s.level, "description": s.description, "availability": s.availability}
                   for s in sorted(user.skills, key=lambda s: s.id)],
    }


@router.get("/members")
def members(search: str = "", category: str = "", limit: int = Query(24, ge=1, le=60),
            offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    query = db.query(User).options(selectinload(User.skills)).filter(User.skills.any())
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.full_name.ilike(term), User.location.ilike(term),
                                 User.skills.any(Skill.title.ilike(term))))
    if category:
        query = query.filter(User.skills.any(Skill.category == category))
    total = query.count()
    users = query.order_by(User.id).offset(offset).limit(limit).all()
    ratings = {uid: (average, count) for uid, average, count in db.query(
        Rating.rated_id, func.avg(Rating.score), func.count(Rating.id)
    ).filter(Rating.rated_id.in_([u.id for u in users])).group_by(Rating.rated_id).all()}
    return {"items": [member_json(u, *ratings.get(u.id, (0, 0))) for u in users], "total": total}


@router.get("/popular-skills")
def popular_skills(limit: int = Query(12, ge=1, le=40), db: Session = Depends(get_db)):
    groups = {}
    for skill in db.query(Skill).order_by(Skill.id).all():
        key = (skill.title.casefold(), skill.category)
        group = groups.setdefault(key, {"title": skill.title, "category": skill.category,
                                       "teachers": set(), "learners": set(), "levels": set()})
        group["teachers" if skill.type == "Offering" else "learners"].add(skill.owner_id)
        if skill.type == "Offering":
            group["levels"].add(skill.level)
    rows = [{"title": g["title"], "category": g["category"], "teachers": len(g["teachers"]),
             "learners": len(g["learners"]), "levels": sorted(g["levels"])} for g in groups.values()]
    return sorted(rows, key=lambda g: (-(g["teachers"] + g["learners"]), g["title"]))[:limit]


@router.get("/members/{member_id}")
def member(member_id: int, db: Session = Depends(get_db)):
    user = db.query(User).options(selectinload(User.skills)).filter(User.id == member_id).first()
    if not user:
        raise HTTPException(404, "Member not found")
    reviews = db.query(Rating, User.full_name).join(User, User.id == Rating.rater_id).filter(
        Rating.rated_id == member_id).order_by(Rating.created_at.desc()).all()
    result = member_json(user, sum(r.score for r, _ in reviews) / len(reviews) if reviews else 0, len(reviews))
    result["reviews"] = [{"id": r.id, "score": r.score, "review": r.review, "author": name}
                         for r, name in reviews[:12]]
    return result
