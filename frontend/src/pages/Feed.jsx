import {useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {Search,Compass,Users,ArrowRight,ArrowRightLeft} from 'lucide-react';
import api,{errorMessage} from '../services/api';
import SkillCard from '../components/SkillCard';
import MemberCard from '../components/MemberCard';
import {SkeletonCard} from '../components/Skeleton';
import {useAuth} from '../context/AuthContext';

export default function Feed() {
  const [params,setParams]=useSearchParams(),{user}=useAuth();
  const [skills,setSkills]=useState([]),[members,setMembers]=useState([]),[total,setTotal]=useState(0),[matches,setMatches]=useState([]);
  const [loading,setLoading]=useState(true),[error,setError]=useState(''),[retry,setRetry]=useState(0);
  const search=params.get('search')||'',category=params.get('category')||'',type=params.get('type')||'',view=params.get('view')==='people'?'people':'skills',page=Number(params.get('page'))||0;
  const change=(key,value)=>{const next=new URLSearchParams(params);value?next.set(key,value):next.delete(key);if(key!=='page')next.delete('page');setParams(next,{replace:true});};
  useEffect(()=>{
    const controller=new AbortController();setLoading(true);setError('');
    const timer=setTimeout(()=>api.get(view==='people'?'/community/members':'/skills',{params:view==='people'?{search,category,limit:24,offset:page*24}:{search,category,skill_type:type},signal:controller.signal}).then(r=>{
      if(view==='people'){setMembers(r.data.items);setTotal(r.data.total);}else{setSkills(r.data);setTotal(r.data.length);}
    }).catch(e=>{if(!controller.signal.aborted)setError(errorMessage(e,'Could not load the community. Please try again.'));}).finally(()=>{if(!controller.signal.aborted)setLoading(false);}),200);
    return()=>{clearTimeout(timer);controller.abort();};
  },[search,category,type,view,page,retry]);
  useEffect(()=>{if(user)api.get('/recommendations').then(r=>setMatches(r.data)).catch(()=>{});else setMatches([]);},[user?.id]);
  return <main className="container explore-page page-transition"><div className="pageintro"><div><span className="eyebrow"><Compass size={14}/> The discovery space</span><h1>A new skill. A new perspective.</h1><p>There’s someone who knows what you want to learn. Find them, and share something in return.</p></div><Link className="button" to={user?'/add-skill':'/register'}>Share your skills <ArrowRight size={16}/></Link></div>
    <div className="explore-toolbar"><div className="category-tabs" aria-label="Explore view"><button aria-pressed={view==='skills'} className={view==='skills'?'active':''} onClick={()=>change('view','skills')}><Compass size={13}/> Skills</button><button aria-pressed={view==='people'} className={view==='people'?'active':''} onClick={()=>change('view','people')}><Users size={13}/> People</button></div><span className="results-count" role="status">{loading?'Finding your next connection…':error?'Community unavailable':total+' '+(view==='people'?'people to learn with':'skill opportunities')}</span></div>
    <div className="filters card"><label className="search"><Search size={18}/><input aria-label={view==='people'?'Search people':'Search skills'} placeholder={view==='people'?'Search a name, city, or skill…':'Try React, design, photography…'} value={search} onChange={e=>change('search',e.target.value)}/></label><select aria-label="Category" value={category} onChange={e=>change('category',e.target.value)}><option value="">All categories</option>{['Technology','Design','Languages','Communication','Business','Creative','Fitness','Cooking','Other'].map(c=><option key={c}>{c}</option>)}</select>{view==='skills'&&<select aria-label="Skill type" value={type} onChange={e=>change('type',e.target.value)}><option value="">Teaching + learning</option><option value="Offering">Can teach</option><option value="Requesting">Wants to learn</option></select>}</div>
    {!search&&!category&&<div className="explore-tip"><ArrowRightLeft size={28}/><div><h2>The best exchanges go both ways.</h2><p>Explore what someone can teach and what they want to learn. You might be just the person they need.</p></div><Link className="text-link" to={user?'/innovation':'/#how-it-works'}>{user?'Find my matches':'See how it works'} <ArrowRight size={15}/></Link></div>}
    {error?<div className="errorbox card" role="alert"><span>{error}</span><button className="button small" onClick={()=>setRetry(n=>n+1)}>Try again</button></div>:loading?<div className="grid">{[1,2,3,4,5,6].map(n=><SkeletonCard key={n}/>)}</div>:<div className={view==='people'?'community-grid':'grid'}>{view==='people'?members.map(m=><MemberCard member={m} key={m.id} match={matches.find(r=>r.skill.owner_id===m.id)?.score}/>):skills.map(s=><SkillCard key={s.id} skill={s} own={s.owner_id===user?.id}/>)}</div>}
    {!loading&&!error&&!(view==='people'?members:skills).length&&<div className="empty card"><Compass size={30}/><h3>A different search could open a new door.</h3><p>Try another skill, a broader category, or a new learning goal.</p><button className="button secondary small" onClick={()=>setParams({view})}>Clear filters</button></div>}
    {view==='people'&&total>24&&!loading&&!error&&<div className="explore-toolbar" style={{marginTop:25}}><button className="button secondary small" disabled={page===0} onClick={()=>change('page',String(page-1))}>Previous</button><span className="results-count">Page {page+1} of {Math.ceil(total/24)}</span><button className="button secondary small" disabled={(page+1)*24>=total} onClick={()=>change('page',String(page+1))}>Next people</button></div>}
  </main>;
}
