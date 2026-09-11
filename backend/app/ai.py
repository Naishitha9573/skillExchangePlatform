import json, os, re, urllib.request
from collections import Counter

STOP={"the","and","for","with","from","this","that","learn","learning","skill","skills","a","an","to","of","in","on","is","are","i","you","want","looking","become","good"}

def tokens(text):
    return {x for x in re.findall(r"[a-z0-9+#.]+",(text or "").lower()) if x not in STOP and len(x)>1}

def local_match_score(source, target):
    a=tokens(" ".join([source.title,source.description,source.tags,source.category]))
    b=tokens(" ".join([target.title,target.description,target.tags,target.category]))
    overlap=len(a&b)/max(1,len(a|b))
    category=1.0 if source.category.lower()==target.category.lower() else 0.0
    return round(min(99,40*overlap+40*category+19),0)

# Backwards-compatible name used throughout the API.
match_score=local_match_score

def explanation(source,target):
    common=tokens(" ".join([source.title,source.tags])) & tokens(" ".join([target.title,target.tags]))
    if common: return f"Strong match: shared focus on {', '.join(sorted(list(common))[:3])}."
    if source.category.lower()==target.category.lower(): return f"Good match: both are in {source.category}."
    return "Potential match based on complementary skills and learning goals."

def _gemini_key():
    return os.getenv("GEMINI_API_KEY", "").strip()

def gemini_json(prompt):
    """Optional live LLM layer. Returns None when no key/network is configured."""
    key=_gemini_key()
    if not key:
        return None
    model=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
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
