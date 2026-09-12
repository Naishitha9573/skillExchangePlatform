import json, re, urllib.request
from app.core.config import settings

STOP={"the","and","for","with","from","this","that","learn","learning","skill","skills","a","an","to","of","in","on","is","are","i","you","want","looking","become","good"}
LEVELS={"Beginner":0,"Intermediate":1,"Advanced":2}
MATCH_WEIGHTS={
    "content_compatibility":25,
    "complementary_skills":25,
    "skill_level_fit":15,
    "reciprocal_benefit":12,
    "reputation":8,
    "successful_interactions":8,
    "behavioral_similarity":7,
}
ALIASES={
    "react.js":"react frontend javascript",
    "reactjs":"react frontend javascript",
    "vue.js":"vue frontend javascript",
    "node.js":"node backend javascript",
    "fastapi":"python backend api",
    "django":"python backend web",
    "javascript":"js frontend web",
    "typescript":"ts javascript frontend",
    "machine learning":"ml ai data",
    "user experience":"ux design",
    "user interface":"ui design",
}

def tokens(text):
    raw=(text or "").lower().replace("/"," ")
    for key,value in ALIASES.items():
        raw=raw.replace(key,value)
    return {x for x in re.findall(r"[a-z0-9+#.]+",raw) if x not in STOP and len(x)>1}

def _text(skill):
    return " ".join([skill.title or "",skill.description or "",skill.tags or "",skill.category or ""])

def _category_score(source,target):
    source_category=(source.category or "").lower()
    target_category=(target.category or "").lower()
    if source_category==target_category:
        return 100
    related={
        "technology":{"technology","business"},
        "design":{"design","creative","technology"},
        "creative":{"creative","design"},
        "business":{"business","communication","technology"},
        "communication":{"communication","languages","business"},
        "languages":{"languages","communication"},
    }
    return 55 if target_category in related.get(source_category,set()) else 0

def _semantic_score(source,target):
    left=tokens(_text(source)); right=tokens(_text(target))
    overlap=len(left & right)/max(1,len(left | right))
    title_overlap=len(tokens(source.title or "") & tokens(target.title or ""))
    return round(min(100,overlap*70+_category_score(source,target)*0.3+min(20,title_overlap*10)),1)

def _level_fit(source,target):
    # The learner is the requesting skill; for a reciprocal pair the learner is target.
    if source.type=="Requesting" and target.type=="Offering":
        learner,teacher=source,target
    elif source.type=="Offering" and target.type=="Requesting":
        learner,teacher=target,source
    else:
        return 35
    delta=LEVELS.get(teacher.level,0)-LEVELS.get(learner.level,0)
    if delta>=1: return 100
    if delta==0: return 72
    return 20

def _complementary_score(source,target):
    return 100 if source.type!=target.type else 15

def _weighted(value,key):
    return value*MATCH_WEIGHTS[key]/100

def hybrid_match(source,target,context=None):
    """Deterministic hybrid score shared by dashboard, reports, and live-match fallback."""
    context=context or {}
    content=_semantic_score(source,target)
    complementary=_complementary_score(source,target)
    level=_level_fit(source,target)
    reciprocal=float(context.get("reciprocal_score",100 if source.type=="Offering" and target.type=="Requesting" else 0))
    reputation=float(context.get("reputation_score",50))
    successful=float(context.get("successful_interaction_score",0))
    behavioral=float(context.get("behavioral_similarity",0)) if context.get("collaborative_available") else 0
    values={"content_compatibility":content,"complementary_skills":complementary,"skill_level_fit":level,"reciprocal_benefit":reciprocal,"reputation":reputation,"successful_interactions":successful,"behavioral_similarity":behavioral}
    score=round(sum(_weighted(value,key) for key,value in values.items()))
    return {"score":max(0,min(100,score)),"breakdown":{key:round(value) for key,value in values.items()},"weights":MATCH_WEIGHTS.copy(),"collaborative_available":bool(context.get("collaborative_available"))}

def match_reasons(source,target,result,context=None):
    context=context or {}
    reasons=[]
    if source.type=="Requesting" and target.type=="Offering":
        reasons.append(f"{target.owner.full_name if getattr(target,'owner',None) else 'This member'} teaches {target.title} while you want to learn it.")
    elif source.type=="Offering" and target.type=="Requesting":
        reasons.append(f"You can teach {source.title}, which {target.owner.full_name if getattr(target,'owner',None) else 'this member'} wants to learn.")
    if result["breakdown"]["skill_level_fit"]>=72:
        reasons.append(f"Level fit: {target.level} teaching for a {source.level} goal.")
    if result["breakdown"]["content_compatibility"]>=55:
        reasons.append(f"Related focus across {source.category} and {target.category}.")
    if result["breakdown"]["reputation"]>50:
        reasons.append(f"Trusted by the community with a {context.get('rating_average',0):g}/5 rating.")
    if result["breakdown"]["behavioral_similarity"]>0:
        reasons.append("Similar learners have engaged with this skill area before.")
    return reasons[:4] or ["A promising fit based on skills, goals, and available community signals."]

def local_match_score(source, target):
    return hybrid_match(source,target)["score"]

# Backwards-compatible name used throughout the API.
match_score=local_match_score

def explanation(source,target):
    result=hybrid_match(source,target)
    return " ".join(match_reasons(source,target,result))

def _gemini_key():
    return settings.GEMINI_API_KEY.strip()

def gemini_json(prompt):
    """Optional live LLM layer. Returns None when no key/network is configured."""
    key=_gemini_key()
    if not key:
        return None
    model=settings.GEMINI_MODEL
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseMimeType":"application/json","temperature":0.2}}
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=12) as response:
            payload=json.loads(response.read().decode())
        text=payload["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception:
        return None

def live_match_analysis(user_profile, candidates):
    prompt=f'''You are the AI matching engine for SkillSwap, a peer-learning platform.
Analyze the learner profile and candidate skills below. Return ONLY valid JSON with this shape:
{{"matches":[{{"candidate_id":number,"score":number,"reason":"short explanation","next_action":"one concrete action"}}]}}
Score from 0-100. Consider semantic meaning, complementary offer/request intent, level, category and practical fit.
Learner: {json.dumps(user_profile)}
Candidates: {json.dumps(candidates)}'''
    return gemini_json(prompt)
