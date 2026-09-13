import secrets
import httpx
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from app.core.config import settings
from app.db import get_db
from app.models import LearningSession, Notification, Profile, Rating, Skill, SkillCatalog, SwapRequest, User
from app.schemas import CoachRequest, GoogleCallback, Login, RatingCreate, SkillCreate, SkillOut, SwapCreate, SwapStatus, Token, UserCreate, UserOut, UserUpdate
from app.auth import hash_password, verify_password, create_token, create_oauth_state, verify_oauth_state, current_user
from app.ai import match_score, explanation, live_match_analysis, tokens, hybrid_match, match_reasons

from app.collaboration import router as collaboration_router, conversation_for, notify, utc_iso
from app.community import router as community_router
from app.realtime import router as realtime_router, hub
from app.db import initialize_database
initialize_database()
app=FastAPI(title=settings.PROJECT_NAME, version="1.0.0", description="AI-powered peer skill exchange platform")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

app.include_router(collaboration_router)
app.include_router(community_router)
app.include_router(realtime_router)

def skill_out(s):
    return SkillOut.model_validate(s)

def recommendation_context(user_id, candidate_id, db, source=None):
    related=db.query(SwapRequest).filter(or_(SwapRequest.requester_id==user_id,SwapRequest.receiver_id==user_id),or_(SwapRequest.requester_id==candidate_id,SwapRequest.receiver_id==candidate_id)).all()
    accepted=sum(x.status in {"accepted","completed"} for x in related)
    completed=sum(x.status=="completed" for x in related)
    ratings=db.query(Rating).filter(Rating.rated_id==candidate_id).all()
    average=sum(x.score for x in ratings)/len(ratings) if ratings else 0
    sessions=db.query(LearningSession).filter(or_(LearningSession.organizer_id==user_id,LearningSession.participant_id==user_id),or_(LearningSession.organizer_id==candidate_id,LearningSession.participant_id==candidate_id),LearningSession.status=="completed").count()
    candidate_interactions=db.query(SwapRequest).filter(or_(SwapRequest.requester_id==candidate_id,SwapRequest.receiver_id==candidate_id),SwapRequest.status.in_(["accepted","completed"])).count()
    collaborative=accepted>=2 and candidate_interactions>=2
    reciprocal=0
    if source:
        opposite="Requesting" if source.type=="Offering" else "Offering"
        reciprocal_skills=db.query(Skill).filter(Skill.owner_id==candidate_id,Skill.type==opposite).all()
        reciprocal=max([hybrid_match(source,candidate_skill)["breakdown"]["content_compatibility"] for candidate_skill in reciprocal_skills] or [0])
    return {"reputation_score":round(average/5*100) if average else 50,"rating_average":round(average,1),"successful_interaction_score":min(100,completed*35+sessions*25+accepted*10),"behavioral_similarity":min(100,accepted*25) if collaborative else 0,"collaborative_available":collaborative,"history_count":accepted+sessions,"reciprocal_score":reciprocal}

def recommendation_row(source,target,context):
    result=hybrid_match(source,target,context)
    return {"score":result["score"],"skill":SkillOut.model_validate(target),"reason":" ".join(match_reasons(source,target,result,context)),"reasons":match_reasons(source,target,result,context),"breakdown":result["breakdown"],"weights":result["weights"],"signals":{"collaborative":result["collaborative_available"],"history_count":context.get("history_count",0),"rating":context.get("rating_average",0)}}

@app.get("/")
def root(): return {"name":settings.PROJECT_NAME,"status":"online","docs":"/docs"}
@app.get("/health")
def health(): return {"status":"healthy"}

@app.get("/api/v1/community/summary")
def community_summary(db:Session=Depends(get_db)):
    completed_sessions=db.query(LearningSession).filter(LearningSession.status=="completed").all()
    return {
        "people": db.query(User).count(),
        "skills": db.query(Skill).count(),
        "teaching_skills": db.query(Skill).filter(Skill.type == "Offering").count(),
        "learning_goals": db.query(Skill).filter(Skill.type == "Requesting").count(),
        "demo": settings.DEMO_MODE,
        "learning_hours": round(sum((session.duration_minutes or 60) for session in completed_sessions) / 60, 1),
    }

@app.post("/api/v1/auth/register",response_model=Token)
def register(data:UserCreate,db:Session=Depends(get_db)):
    if db.query(User).filter(func.lower(User.email)==data.email).first(): raise HTTPException(409,"Email already registered")
    u=User(email=data.email,password_hash=hash_password(data.password),full_name=data.full_name,location=data.location,profile=Profile(location=data.location))
    db.add(u); db.commit(); db.refresh(u)
    return {"access_token":create_token(u.id),"user":u}
@app.post("/api/v1/auth/login",response_model=Token)
def login(data:Login,db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==data.email).first()
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
    return {"access_token":create_token(u.id),"user":u}

@app.get("/api/v1/auth/google/authorize")
def google_authorize(response:Response):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(503,"Google sign-in requires GOOGLE_CLIENT_ID in backend/.env")
    if not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(503,"Google sign-in requires GOOGLE_REDIRECT_URI in backend/.env")
    from urllib.parse import urlencode
    state=create_oauth_state()
    secure=settings.GOOGLE_REDIRECT_URI.startswith("https://")
    response.set_cookie("skillswap_oauth_state",state,httponly=True,secure=secure,samesite="none" if secure else "lax",max_age=600,path="/api/v1/auth/google/callback")
    response.headers["Cache-Control"]="no-store"
    params={"client_id":settings.GOOGLE_CLIENT_ID,"redirect_uri":settings.GOOGLE_REDIRECT_URI,"response_type":"code","scope":"openid email profile","state":state,"prompt":"select_account"}
    return {"authorization_url":"https://accounts.google.com/o/oauth2/v2/auth?"+urlencode(params)}

@app.post("/api/v1/auth/google/callback",response_model=Token)
def google_callback(data:GoogleCallback,request:Request,response:Response,db:Session=Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(503,"Google sign-in requires GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI in backend/.env")
    try:
        if not secrets.compare_digest(request.cookies.get("skillswap_oauth_state", ""), data.state):
            raise ValueError("OAuth browser session does not match")
        verify_oauth_state(data.state)
    except Exception:
        raise HTTPException(400,"Google sign-in session expired or is invalid")
    try:
        with httpx.Client(timeout=10) as client:
            token_response=client.post("https://oauth2.googleapis.com/token",data={"code":data.code,"client_id":settings.GOOGLE_CLIENT_ID,"client_secret":settings.GOOGLE_CLIENT_SECRET,"redirect_uri":settings.GOOGLE_REDIRECT_URI,"grant_type":"authorization_code"})
            token_response.raise_for_status()
            access_token=token_response.json().get("access_token")
            if not access_token: raise ValueError("Missing Google access token")
            profile_response=client.get("https://openidconnect.googleapis.com/v1/userinfo",headers={"Authorization":f"Bearer {access_token}"})
            profile_response.raise_for_status()
            profile=profile_response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(400,"Google could not verify your account")
    email=str(profile.get("email","")).strip().lower()
    if not email or profile.get("email_verified") is not True: raise HTTPException(400,"Google account email is not verified")
    user=db.query(User).filter(func.lower(User.email)==email).first()
    if not user:
        name=str(profile.get("name") or email.split("@")[0]).strip()[:120]
        user=User(email=email,password_hash=hash_password(secrets.token_urlsafe(32)),full_name=name,avatar_url=profile.get("picture","") or "",profile=Profile(avatar_url=profile.get("picture","") or ""))
        db.add(user); db.commit(); db.refresh(user)
    response.delete_cookie("skillswap_oauth_state",path="/api/v1/auth/google/callback")
    response.headers["Cache-Control"]="no-store"
    return {"access_token":create_token(user.id),"user":user}

@app.get("/api/v1/auth/providers")
def auth_providers():
    return {"google":bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_REDIRECT_URI)}
@app.get("/api/v1/users/me",response_model=UserOut)
def me(user:User=Depends(current_user)): return user
@app.put("/api/v1/users/me",response_model=UserOut)
def update_me(data:UserUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not user.profile: user.profile=Profile()
    for k,v in data.model_dump(exclude_none=True).items():
        setattr(user,k,v)
        if k in {"bio","location","avatar_url"}: setattr(user.profile,k,v)
    db.commit(); db.refresh(user); return user

@app.get("/api/v1/skills",response_model=list[SkillOut])
def list_skills(search:str="",category:str="",skill_type:str="",db:Session=Depends(get_db)):
    q=db.query(Skill).options(joinedload(Skill.owner)).order_by(Skill.created_at.desc())
    if search:
        term=f"%{search}%"; q=q.filter(or_(Skill.title.ilike(term),Skill.description.ilike(term),Skill.tags.ilike(term),Skill.category.ilike(term)))
    if category: q=q.filter(Skill.category==category)
    if skill_type: q=q.filter(Skill.type==skill_type)
    return q.limit(100).all()
@app.get("/api/v1/skills/mine",response_model=list[SkillOut])
def my_skills(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return db.query(Skill).options(joinedload(Skill.owner)).filter(Skill.owner_id==user.id).order_by(Skill.created_at.desc()).all()

@app.get("/api/v1/skills/{skill_id}",response_model=SkillOut)
def get_skill(skill_id:int,db:Session=Depends(get_db)):
    s=db.query(Skill).options(joinedload(Skill.owner)).filter(Skill.id==skill_id).first()
    if not s: raise HTTPException(404,"Skill not found")
    return s
@app.post("/api/v1/skills",response_model=SkillOut)
def create_skill(data:SkillCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if data.type not in {"Offering","Requesting"}: raise HTTPException(400,"type must be Offering or Requesting")
    values=data.model_dump()
    catalog=db.query(SkillCatalog).filter(SkillCatalog.name==values["title"],SkillCatalog.category==values["category"]).first()
    if not catalog: catalog=SkillCatalog(name=values["title"],category=values["category"]); db.add(catalog); db.flush()
    s=Skill(owner_id=user.id,catalog_id=catalog.id,**values); db.add(s); db.commit(); db.refresh(s); return db.query(Skill).options(joinedload(Skill.owner)).get(s.id)
@app.delete("/api/v1/skills/{skill_id}")
def delete_skill(skill_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    s=db.get(Skill,skill_id)
    if not s: raise HTTPException(404,"Skill not found")
    if s.owner_id!=user.id: raise HTTPException(403,"Not your skill")
    if db.query(SwapRequest.id).filter(or_(SwapRequest.offered_skill_id==s.id,SwapRequest.requested_skill_id==s.id)).first():
        raise HTTPException(409,"This skill belongs to an exchange and must be kept in its history")
    db.delete(s); db.commit(); return {"message":"Skill deleted"}

@app.get("/api/v1/recommendations")
def recommendations(user:User=Depends(current_user),db:Session=Depends(get_db)):
    mine=db.query(Skill).filter(Skill.owner_id==user.id).all()
    if not mine: return []
    others=db.query(Skill).options(joinedload(Skill.owner)).filter(Skill.owner_id!=user.id).all()
    out=[]
    for target in others:
        best=None
        for source in mine:
            row=recommendation_row(source,target,recommendation_context(user.id,target.owner_id,db,source))
            if best is None or row["score"]>best[0]: best=(row["score"],source,row)
        if best:
            out.append(best[2])
    return sorted(out,key=lambda x:x["score"],reverse=True)[:12]

@app.get("/api/v1/dashboard")
def dashboard(user:User=Depends(current_user),db:Session=Depends(get_db)):
    offered=db.query(Skill).filter(Skill.owner_id==user.id,Skill.type=="Offering").count()
    requested=db.query(Skill).filter(Skill.owner_id==user.id,Skill.type=="Requesting").count()
    incoming=db.query(SwapRequest).filter(SwapRequest.receiver_id==user.id,SwapRequest.status=="pending").count()
    outgoing=db.query(SwapRequest).filter(SwapRequest.requester_id==user.id,SwapRequest.status=="pending").count()
    completed=db.query(SwapRequest).filter(or_(SwapRequest.requester_id==user.id,SwapRequest.receiver_id==user.id),SwapRequest.status=="completed").count()
    rating=db.query(func.avg(Rating.score)).filter(Rating.rated_id==user.id).scalar()
    ratings_count=db.query(Rating).filter(Rating.rated_id==user.id).count()
    swaps_count=db.query(SwapRequest).filter(or_(SwapRequest.requester_id==user.id,SwapRequest.receiver_id==user.id)).count()
    xp=offered*80+requested*60+completed*150+ratings_count*25+min(swaps_count,10)*10
    level=max(1,xp//300+1)
    badges=[]
    if offered>=1: badges.append({"id":"teacher","name":"First Teacher","icon":"🎓","description":"Shared your first skill."})
    if requested>=1: badges.append({"id":"learner","name":"Curious Learner","icon":"🧠","description":"Added a learning goal."})
    if completed>=1: badges.append({"id":"connector","name":"Skill Connector","icon":"🤝","description":"Completed your first swap."})
    if ratings_count>=3: badges.append({"id":"trusted","name":"Trusted Mentor","icon":"⭐","description":"Received multiple ratings."})
    return {"offered":offered,"requested":requested,"incoming":incoming,"outgoing":outgoing,"completed":completed,"rating":round(rating or 0,1),"xp":xp,"level":level,"next_level_xp":level*300,"badges":badges,"streak":min(7,completed+ratings_count)}

@app.post("/api/v1/swaps",response_model=dict)
def create_swap(data:SwapCreate,tasks:BackgroundTasks,user:User=Depends(current_user),db:Session=Depends(get_db)):
    offered=db.get(Skill,data.offered_skill_id); requested=db.get(Skill,data.requested_skill_id)
    if not offered or not requested: raise HTTPException(404,"Skill not found")
    if offered.owner_id!=user.id: raise HTTPException(403,"Offered skill must belong to you")
    if requested.owner_id==user.id: raise HTTPException(400,"Choose another user's requested skill")
    if offered.type!="Offering": raise HTTPException(400,"Choose one of your offered skills")
    receiver_id=requested.owner_id
    if data.receiver_id!=receiver_id: raise HTTPException(400,"Receiver does not own the requested skill")
    exists=db.query(SwapRequest).filter(SwapRequest.requester_id==user.id,SwapRequest.requested_skill_id==requested.id,SwapRequest.status=="pending").first()
    if exists: raise HTTPException(409,"A pending request already exists")
    r=SwapRequest(requester_id=user.id,receiver_id=receiver_id,offered_skill_id=offered.id,requested_skill_id=requested.id,message=data.message)
    db.add(r); notify(db, receiver_id, "New swap proposal", f"{user.full_name} proposed a skill exchange.", "swap"); db.commit(); db.refresh(r)
    tasks.add_task(hub.publish, [user.id, receiver_id], {"type":"swaps.changed"})
    tasks.add_task(hub.publish, [receiver_id], {"type":"notifications.changed"})
    return {"id":r.id,"status":r.status,"message":"Swap request sent"}

def swap_json(r):
    return {"id":r.id,"status":r.status,"message":r.message,"created_at":r.created_at,"requester":{"id":r.requester.id,"full_name":r.requester.full_name,"email":r.requester.email},"receiver":{"id":r.receiver.id,"full_name":r.receiver.full_name},"offered_skill":{"id":r.offered_skill.id,"title":r.offered_skill.title},"requested_skill":{"id":r.requested_skill.id,"title":r.requested_skill.title}}
@app.get("/api/v1/swaps")
def swaps(user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(SwapRequest).options(joinedload(SwapRequest.requester),joinedload(SwapRequest.receiver),joinedload(SwapRequest.offered_skill),joinedload(SwapRequest.requested_skill)).filter(or_(SwapRequest.requester_id==user.id,SwapRequest.receiver_id==user.id)).order_by(SwapRequest.created_at.desc()).all()
    return [swap_json(r) for r in rows]
@app.patch("/api/v1/swaps/{swap_id}")
def update_swap(swap_id:int,data:SwapStatus,tasks:BackgroundTasks,user:User=Depends(current_user),db:Session=Depends(get_db)):
    r=db.query(SwapRequest).filter(SwapRequest.id==swap_id).first()
    if not r: raise HTTPException(404,"Request not found")
    if r.receiver_id!=user.id and r.requester_id!=user.id: raise HTTPException(403,"Not your request")

    target=data.status.strip().lower()
    if target not in {"accepted","rejected","cancelled","completed"}:
        raise HTTPException(400,"Invalid status")

    current=r.status
    if target in {"accepted","rejected"} and r.receiver_id!=user.id:
        raise HTTPException(403,"Only the receiver can accept or reject")
    if target=="cancelled" and r.requester_id!=user.id:
        raise HTTPException(403,"Only the requester can cancel a pending swap")
    if target=="completed" and user.id not in {r.requester_id,r.receiver_id}:
        raise HTTPException(403,"Only swap participants can complete the swap")

    allowed={
        "pending":{"accepted","rejected","cancelled"},
        "accepted":{"completed"},
        "rejected":set(),
        "cancelled":set(),
        "completed":set(),
    }
    if target not in allowed.get(current,set()):
        raise HTTPException(409,f"Cannot change a {current} swap to {target}")

    r.status=target
    if target == "accepted":
        conversation_for(db, r.requester_id, r.receiver_id)
    recipient_id=r.requester_id if user.id==r.receiver_id else r.receiver_id
    notify(db, recipient_id, "Swap updated", f"Your swap request is now {target}.", "swap")
    db.commit()
    tasks.add_task(hub.publish, [r.requester_id, r.receiver_id], {"type":"swaps.changed"})
    tasks.add_task(hub.publish, [r.requester_id, r.receiver_id], {"type":"conversations.changed"})
    tasks.add_task(hub.publish, [recipient_id], {"type":"notifications.changed"})
    return {"message":f"Request {target}","status":r.status}

@app.post("/api/v1/ratings/{swap_id}")
def rate(swap_id:int,data:RatingCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    r=db.get(SwapRequest,swap_id)
    if not r or r.status != "completed": raise HTTPException(400,"Complete the swap before leaving a review")
    rated=r.receiver_id if r.requester_id==user.id else r.requester_id
    if user.id not in {r.requester_id,r.receiver_id}: raise HTTPException(403,"Not part of swap")
    if db.query(Rating).filter(Rating.rater_id==user.id,Rating.swap_id==swap_id).first(): raise HTTPException(409,"Already rated")
    x=Rating(rater_id=user.id,rated_id=rated,swap_id=swap_id,score=data.score,review=data.review); db.add(x); db.commit(); return {"message":"Rating submitted"}

@app.get("/api/v1/ratings")
def my_ratings(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"swap_id":r.swap_id,"score":r.score,"review":r.review} for r in db.query(Rating).filter(Rating.rater_id==user.id).all()]

@app.get("/api/v1/notifications")
def notifications(user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Notification).filter(Notification.user_id==user.id).order_by(Notification.created_at.desc()).limit(30).all()
    return [{"id":n.id,"title":n.title,"body":n.body,"kind":n.kind,"read":bool(n.read),"created_at":utc_iso(n.created_at)} for n in rows]

@app.patch("/api/v1/notifications/{notification_id}/read")
def read_notification(notification_id:int,tasks:BackgroundTasks,user:User=Depends(current_user),db:Session=Depends(get_db)):
    n=db.query(Notification).filter(Notification.id==notification_id,Notification.user_id==user.id).first()
    if not n: raise HTTPException(404,"Notification not found")
    n.read=1; db.commit()
    tasks.add_task(hub.publish, [user.id], {"type":"notifications.changed"})
    return {"message":"Notification marked read"}

@app.get("/api/v1/leaderboard")
def leaderboard(db:Session=Depends(get_db)):
    rows=[]
    for u in db.query(User).all():
        offered=db.query(Skill).filter(Skill.owner_id==u.id,Skill.type=="Offering").count()
        completed=db.query(SwapRequest).filter(or_(SwapRequest.requester_id==u.id,SwapRequest.receiver_id==u.id),SwapRequest.status=="completed").count()
        avg=db.query(func.avg(Rating.score)).filter(Rating.rated_id==u.id).scalar() or 0
        xp=offered*80+completed*150+round(avg*20)
        rows.append({"user_id":u.id,"name":u.full_name,"location":u.location,"xp":xp,"level":max(1,xp//300+1),"rating":round(avg,1),"completed":completed,"skills":offered})
    return sorted(rows,key=lambda x:(x["xp"],x["rating"]),reverse=True)[:20]

@app.post("/api/v1/coach")
def coach(data:CoachRequest,user:User=Depends(current_user),db:Session=Depends(get_db)):
    target=data.target_skill.strip(); current=[x.strip() for x in data.current_skills.split(",") if x.strip()]
    probe=Skill(title=target,description=data.goal,tags=','.join(current),category="Technology")
    matched=[]
    for s in db.query(Skill).filter(Skill.type=="Offering",Skill.owner_id!=user.id).all():
        score=match_score(probe,s)
        if score>=35: matched.append({"title":s.title,"owner":s.owner.full_name if s.owner else "Community mentor","score":int(score)})
    matched=sorted(matched,key=lambda x:x["score"],reverse=True)[:5]
    phases=[
      {"week":"Week 1","focus":"Foundations","actions":[f"Define what good {target} looks like","Learn core concepts and vocabulary","Build one tiny practice task"]},
      {"week":"Week 2","focus":"Guided practice","actions":["Follow a real example","Pair with a community mentor","Complete a small challenge"]},
      {"week":"Week 3","focus":"Project sprint","actions":[f"Build a mini project using {target}","Ask for peer feedback","Document what you learned"]},
      {"week":"Week 4","focus":"Proof & teaching","actions":["Polish your project","Share your result with the community","Teach one concept to another learner"]}
    ]
    return {"target":target,"goal":data.goal,"current_skills":current,"plan":phases,"mentor_matches":matched,"tip":f"Your fastest path is to combine {target} practice with a real peer exchange. Aim for 3 focused sessions per week."}

# ---------------- Hackathon Innovation APIs ----------------
@app.get("/api/v1/innovation/impact")
def innovation_impact(user:User=Depends(current_user),db:Session=Depends(get_db)):
    mine=db.query(Skill).filter(Skill.owner_id==user.id).all()
    swaps=db.query(SwapRequest).filter(or_(SwapRequest.requester_id==user.id,SwapRequest.receiver_id==user.id)).all()
    completed=[x for x in swaps if x.status=="completed"]
    ratings=db.query(Rating).filter(Rating.rated_id==user.id).all()
    session_rows=db.query(LearningSession).filter(or_(LearningSession.organizer_id==user.id,LearningSession.participant_id==user.id),LearningSession.status=="completed").all()
    hours=round(sum((x.duration_minutes or 60)/60 for x in session_rows),1)
    people=len({x.receiver_id if x.requester_id==user.id else x.requester_id for x in swaps})
    knowledge_points=sum(20 if x.type=="Offering" else 10 for x in mine)+len(completed)*50
    return {"skills_shared":sum(x.type=="Offering" for x in mine),"learning_goals":sum(x.type=="Requesting" for x in mine),"people_connected":people,"sessions_completed":len(session_rows),"learning_hours":hours,"knowledge_points":knowledge_points,"average_rating":round(sum(x.score for x in ratings)/len(ratings),1) if ratings else 0,"impact_message":f"You have contributed approximately {hours:g} community learning hour(s). Keep exchanging to grow your impact."}

@app.post("/api/v1/ai/match-report")
def match_report(data:CoachRequest,user:User=Depends(current_user),db:Session=Depends(get_db)):
    probe=Skill(title=data.target_skill,description=data.goal,tags=data.current_skills,category="Technology",type="Requesting",level="Beginner")
    rows=[]
    for target in db.query(Skill).options(joinedload(Skill.owner)).filter(Skill.owner_id!=user.id).all():
        context=recommendation_context(user.id,target.owner_id,db,probe)
        rows.append(recommendation_row(probe,target,context))
    return sorted(rows,key=lambda x:x["score"],reverse=True)[:8]

@app.post("/api/v1/ai/skill-gap")
def skill_gap(data:CoachRequest,user:User=Depends(current_user),db:Session=Depends(get_db)):
    current=tokens(data.current_skills); target=tokens(data.target_skill+" "+data.goal)
    gaps=sorted(target-current)[:8]
    requested=[x.title for x in db.query(Skill).filter(Skill.owner_id==user.id,Skill.type=="Requesting").all()]
    return {"target":data.target_skill,"gap_keywords":gaps,"priority":"High" if len(gaps)>=4 else "Medium","readiness":max(25,100-len(gaps)*10),"next_steps":[f"Build one practical {data.target_skill} mini-project","Find a peer mentor for the biggest gap","Schedule two focused practice sessions this week","Teach one concept back to the community"],"existing_learning_goals":requested,"insight":"AI compared your stated goal with your current skills and surfaced the concepts most likely to unlock progress."}

@app.get("/api/v1/ai/verification-quiz")
def verification_quiz(skill:str=Query(...,min_length=2),user:User=Depends(current_user)):
    key=skill.lower()
    bank={
      "python":[("What does a Python list comprehension primarily provide?",["Compact list creation","Database indexing","HTTP routing","GPU acceleration"],0),("Which keyword defines a function?",["func","def","lambda-only","method"],1),("What is commonly used to handle exceptions?",["try/except","if/else only","switch","catch-only"],0)],
      "react":[("What hook manages local component state?",["useState","useRoute","useSQL","useFetch"],0),("What is JSX?",["JavaScript syntax extension","Database","CSS preprocessor","Python package"],0),("Which prop pattern helps render lists?",["key","indexDB","primary","foreign"],0)],
      "sql":[("Which clause filters rows?",["WHERE","GROUP","ORDER","JOIN"],0),("Which command reads data?",["SELECT","PUSH","FETCHALL","READ"],0),("What does a primary key provide?",["Unique row identity","Encryption","Sorting only","Caching"],0)]
    }
    chosen=next((v for k,v in bank.items() if k in key),bank["python"]+bank["sql"][:1])
    return {"skill":skill,"questions":[{"id":i+1,"question":q,"options":opts} for i,(q,opts,_) in enumerate(chosen)]}

@app.post("/api/v1/ai/verification-result")
def verification_result(skill:str,answers:list[int],user:User=Depends(current_user)):
    key=skill.lower(); correct={"python":[0,1,0],"react":[0,0,0],"sql":[0,0,0]}
    expected=next((v for k,v in correct.items() if k in key),[0,1,0])
    score=round(sum(a==b for a,b in zip(answers,expected))/max(1,len(expected))*100)
    return {"skill":skill,"score":score,"verified":score>=67,"badge":"Skill Verified" if score>=67 else "Practice More","message":"You demonstrated a strong foundation. Add the verified badge to your profile." if score>=67 else "Keep practicing and retake the verification challenge."}

@app.post("/api/v1/ai/live-match")
def live_ai_match(data:CoachRequest,user:User=Depends(current_user),db:Session=Depends(get_db)):
    candidates=db.query(Skill).options(joinedload(Skill.owner)).filter(Skill.owner_id!=user.id,Skill.type=="Offering").all()
    candidate_payload=[{"candidate_id":s.id,"title":s.title,"owner":s.owner.full_name if s.owner else "Community mentor","category":s.category,"description":s.description,"tags":s.tags,"level":s.level} for s in candidates[:30]]
    profile={"target_skill":data.target_skill,"current_skills":data.current_skills,"goal":data.goal}
    live=live_match_analysis(profile,candidate_payload)
    # Deterministic scores remain authoritative; Gemini can improve wording without
    # changing database-driven ranking or making the feature require an API key.
    probe=Skill(title=data.target_skill,description=data.goal,tags=data.current_skills,category="Technology",type="Requesting",level="Beginner")
    contexts={s.id:recommendation_context(user.id,s.owner_id,db,probe) for s in candidates}
    rows=[]
    for s in candidates:
        row=recommendation_row(probe,s,contexts[s.id])
        row.update({"next_action":"Open the skill and propose a swap.","provider":"Local hybrid matcher"})
        rows.append(row)
    if live and isinstance(live.get("matches"),list):
        ai_by_id={m.get("candidate_id"):m for m in live["matches"]}
        for row in rows:
            ai=ai_by_id.get(row["skill"].id)
            if ai and ai.get("reason"):
                row["reason"]=f"{row['reason']} AI context: {ai['reason']}"
                row["provider"]="Hybrid matcher + Gemini explanation"
    return {"provider":"Hybrid matcher + Gemini explanation" if live else "Local hybrid matcher","matches":sorted(rows,key=lambda x:x["score"],reverse=True)[:6]}

@app.get("/api/v1/judge/summary")
def judge_summary(user:User=Depends(current_user),db:Session=Depends(get_db)):
    total_users=db.query(User).count(); total_skills=db.query(Skill).count(); total_swaps=db.query(SwapRequest).count()
    completed=db.query(SwapRequest).filter(SwapRequest.status=="completed").count()
    sessions=db.query(LearningSession).filter(LearningSession.status=="completed").all()
    hours=round(sum((x.duration_minutes or 60)/60 for x in sessions),1)
    ratings=db.query(Rating).all()
    avg=round(sum(x.score for x in ratings)/len(ratings),1) if ratings else 0
    return {"users":total_users,"skills":total_skills,"swaps":total_swaps,"completed_swaps":completed,"learning_hours":hours,"average_rating":avg,"ai_provider":"Gemini" if settings.GEMINI_API_KEY else "Local semantic matcher","demo_accounts":[{"email":"ananya@demo.com","password":"demo123","story":"React mentor → Python learner"},{"email":"rahul@demo.com","password":"demo123","story":"Python mentor → React learner"}] if settings.DEMO_MODE else [],"demo_flow":["Discover","AI Match","Swap","Message","Schedule","Learn","Complete","Rate"]}

@app.get("/api/v1/challenges")
def challenges(user:User=Depends(current_user)):
    return [
      {"id":"teach-60","title":"Teach in 60 Minutes","icon":"🎓","description":"Help another learner master one practical concept in a one-hour exchange.","xp":150,"difficulty":"Community","metric":"1 completed session"},
      {"id":"build-week","title":"7-Day Build Sprint","icon":"🚀","description":"Turn one skill into a tiny portfolio project and share your result.","xp":250,"difficulty":"Intermediate","metric":"1 project shipped"},
      {"id":"mentor-three","title":"Knowledge Multiplier","icon":"🤝","description":"Complete three meaningful peer exchanges and collect feedback.","xp":400,"difficulty":"Advanced","metric":"3 completed swaps"},
      {"id":"skill-chain","title":"Skill Chain","icon":"🔗","description":"Learn one skill from a peer, then teach a connected skill to someone else.","xp":300,"difficulty":"AI Challenge","metric":"learn → teach loop"}
    ]
