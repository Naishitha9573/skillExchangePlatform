import {useCallback,useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {ArrowRight,ArrowUpRight,Plus,Users,Star,Clock3,CheckCircle2,MessageCircle,CalendarDays,BookOpen,GraduationCap,Target} from 'lucide-react';
import api from '../services/api';
import SkillCard from '../components/SkillCard';
import {Avatar} from '../components/MemberCard';
import AnimatedCounter from '../components/AnimatedCounter';
import {SkeletonCard,SkeletonStat} from '../components/Skeleton';
import {useAuth} from '../context/AuthContext';
import {useRealtime} from '../context/RealtimeContext';
import {asDate,dateTime} from '../services/dates';

export default function Dashboard() {
  const {user}=useAuth(),{subscribe}=useRealtime();
  const [stats,setStats]=useState(null),[rec,setRec]=useState([]),[skills,setSkills]=useState([]),[sessions,setSessions]=useState([]),[swaps,setSwaps]=useState([]),[conversations,setConversations]=useState([]);
  const [loading,setLoading]=useState(true),[error,setError]=useState('');
  const load=useCallback(async()=>{
    const results=await Promise.allSettled(['/dashboard','/recommendations','/skills/mine','/sessions','/swaps','/conversations'].map(path=>api.get(path)));
    const setters=[setStats,setRec,setSkills,setSessions,setSwaps,setConversations];
    results.forEach((r,i)=>{if(r.status==='fulfilled')setters[i](r.value.data);});
    setError(results.some(r=>r.status==='rejected')?'Some of your activity could not be refreshed. Please try again.':'');
    setLoading(false);
  },[user.id]);
  useEffect(()=>{load();},[load]);
  useEffect(()=>subscribe(event=>{if(['swaps.changed','session.updated','message.created','messages.read'].includes(event.type))load();}),[subscribe,load]);
  const hour=new Date().getHours(),greeting=hour<12?'Good morning':hour<17?'Good afternoon':'Good evening';
  const teaching=skills.filter(s=>s.type==='Offering'),goals=skills.filter(s=>s.type==='Requesting');
  const upcoming=sessions.filter(s=>s.status==='scheduled'&&asDate(s.scheduled_at).getTime()+s.duration_minutes*60000>Date.now()).sort((a,b)=>asDate(a.scheduled_at)-asDate(b.scheduled_at));
  const next=upcoming[0],nextPartner=next&&(next.organizer.id===user.id?next.participant:next.organizer);
  const activeSwaps=swaps.filter(s=>['pending','accepted'].includes(s.status));
  const unread=conversations.filter(c=>c.unread_count>0);
  const progress=Math.round(((stats?.xp||0)%300)/3);
  return <main className="container dashboard-page page-transition">
    <section className="dashhero"><div><span className="eyebrow"><Users size={14}/> Your learning space</span><h1>{greeting}, {user.full_name.split(' ')[0]}.</h1><p>Make a little room for something new. Your next connection could change what you know.</p><div className="quick-actions"><Link to="/feed?view=people"><Users size={14}/> Explore people</Link><Link to="/add-skill"><Plus size={14}/> Add a skill</Link><Link to="/sessions"><CalendarDays size={14}/> Schedule a session</Link></div></div><Link className="button" to="/innovation">Find my matches <ArrowUpRight size={16}/></Link></section>
    {error&&<div className="errorbox" role="alert"><span>{error}</span><button className="button small" onClick={load}>Try again</button></div>}
    {!loading&&!error&&(!teaching.length||!goals.length)&&<div className="onboarding-strip"><Target size={24}/><div><strong>Give your next match a starting point.</strong><p>{!teaching.length?'Add a skill you can teach. Your experience is worth sharing.':'Add a learning goal to find people who can help you grow.'}</p></div><Link className="button small" to={!teaching.length?'/add-skill':'/add-skill?type=Requesting'}>Complete your exchange profile <ArrowRight size={14}/></Link></div>}
    <div className="stats">{loading?[1,2,3,4,5].map(n=><SkeletonStat key={n}/>):[['Skills you teach',stats?.offered,GraduationCap],['Learning goals',stats?.requested,BookOpen],['Active swaps',error?undefined:activeSwaps.length,Clock3],['Completed swaps',stats?.completed,CheckCircle2],['Your rating',stats?.rating||'—',Star]].map(([label,value,Icon])=><div className="stat card" key={label}><Icon size={20}/><div><span>{label}</span><strong>{value==null?'—':typeof value==='number'?<AnimatedCounter to={value} decimals={label==='Your rating'?1:0}/>:value}</strong></div></div>)}</div>
    <div className="dashboard-layout"><div className="dashboard-main">
      <section className="section"><div className="sectionhead"><div><h2>Best matches for you</h2><p>Find someone whose strengths meet your goals.</p></div><Link to="/innovation">See matches <ArrowRight size={15}/></Link></div>{loading?<div className="grid">{[1,2].map(n=><SkeletonCard key={n}/>)}</div>:rec.length?<div className="grid">{rec.slice(0,4).map(r=><SkillCard key={r.skill.id} skill={r.skill} match={r.score} reason={r.reason} signals={r.signals}/>)}</div>:<div className="empty card"><Target size={29}/><h3>Your next learning partner starts with you.</h3><p>Tell the community what you can teach and what you’d like to learn. Your recommendations will grow from there.</p><Link className="button small" to="/add-skill">Add your skills <ArrowRight size={14}/></Link></div>}</section>
      <div className="dashboard-goals">{[['Skills you teach',teaching,'Offering'],['Your learning goals',goals,'Requesting']].map(([title,rows,type])=><section className="card" key={title}><h2>{title}</h2>{rows.slice(0,3).map(s=><Link className="dashboard-mini-row" key={s.id} to={'/skill/'+s.id}><div><strong>{s.title}</strong><small>{s.level} · {s.category}</small></div><ArrowUpRight size={14}/></Link>)}{!rows.length&&<p>{loading?'Loading your skills…':type==='Offering'?'Your everyday know-how can be someone else’s breakthrough.':'Pick one thing you have always wanted to try.'}</p>}<Link className="text-link" to={'/add-skill?type='+type}><Plus size={13}/>{type==='Offering'?'Share a skill':'Add a learning goal'}</Link></section>)}</div>
      <section className="gamify card"><div className="levelcircle"><span>LEVEL</span><strong>{stats?.level||'—'}</strong></div><div className="xpinfo"><div className="sectionhead"><div><h2>Your knowledge, making an impact</h2><p>{stats?stats.xp+' XP earned':'Loading progress…'} · Every exchange moves you forward.</p></div><span className="match">{progress}% to next level</span></div><div className="progressbar" role="progressbar" aria-label="Progress to next level" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}><span style={{width:progress+'%'}}/></div><div className="badges">{stats?.badges?.map(b=><span title={b.description} key={b.id}>{b.icon} {b.name}</span>)}{!stats?.badges?.length&&<span>Share your first skill to earn a teaching badge</span>}</div></div></section>
    </div><aside className="dashboard-aside">
      <section className="card next-session"><span className="section-kicker">Make time for your next chapter</span><h2 style={{marginTop:12}}>Your next session</h2><CalendarDays size={25}/><h3>{next?.topic||(loading?'Opening your calendar…':'A new skill starts with a date.')}</h3>{next?<><p>with {nextPartner.name} · {next.duration_minutes} minutes</p><time>{dateTime(next.scheduled_at)}</time><Link className="button light-button full" to={next.call_available?'/sessions/'+next.id+'/call':'/sessions'}>{next.call_available?'Join learning session':'View your schedule'} <ArrowRight size={15}/></Link></>:<><p>Choose a time with an accepted exchange partner and turn your plans into progress.</p><Link className="button light-button full" to="/sessions">Plan a session <ArrowRight size={14}/></Link></>}</section>
      <section className="card"><h2><MessageCircle size={17}/> Your conversations</h2>{(unread.length?unread:conversations).slice(0,3).map(c=><Link className="dashboard-mini-row" key={c.id} to={'/messages/'+c.partner.id}><Avatar person={c.partner}/><div><strong>{c.partner.full_name}</strong><small>{c.unread_count?c.unread_count+' unread messages':'Continue your conversation'}</small></div><ArrowUpRight size={14}/></Link>)}{!conversations.length&&<p className="aside-note">{loading?'Loading conversations…':'A friendly hello is all it takes. Propose an exchange to start a conversation.'}</p>}<Link className="text-link" to="/messages">Open messages <ArrowRight size={14}/></Link></section>
      <section className="card"><h2>Exchanges in motion</h2>{activeSwaps.slice(0,3).map(s=><Link className="dashboard-mini-row" to="/swaps" key={s.id}><div><strong>{s.receiver.id===user.id?s.requester.full_name:s.receiver.full_name}</strong><small>{s.offered_skill.title} ↔ {s.requested_skill.title}</small></div><span className={'status '+s.status}>{s.status}</span></Link>)}{!activeSwaps.length&&<p className="aside-note">{loading?'Loading exchanges…':'Find a skill that interests you and offer a little of your own knowledge in return.'}</p>}<Link className="text-link" to="/swaps">View your swaps <ArrowRight size={14}/></Link></section>
    </aside></div>
  </main>;
}
