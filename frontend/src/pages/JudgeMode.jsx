import {useEffect,useState} from 'react';
import {ArrowRight,BrainCircuit,CheckCircle2,MessageCircle,Presentation,RefreshCw,Sparkles,Target,Users,Zap} from 'lucide-react';
import {Link} from 'react-router-dom';
import api from '../services/api';

const STEPS=[
 ['01','Discover','Find a real skill someone can teach or wants to learn.','/feed',Target],
 ['02','AI Match','Show an explainable match score and the reason behind it.','/innovation',BrainCircuit],
 ['03','Exchange','Send, accept and complete a skill swap.','/swaps',Zap],
 ['04','Collaborate','Message the partner and schedule a focused session.','/messages',MessageCircle],
 ['05','Impact','Complete, rate and measure learning impact.','/innovation',CheckCircle2]
];
export default function JudgeMode(){
 const [summary,setSummary]=useState(null); const [loading,setLoading]=useState(true);
 const load=()=>{setLoading(true);api.get('/judge/summary').then(r=>setSummary(r.data)).catch(console.error).finally(()=>setLoading(false))};
 useEffect(()=>{load()},[]);
 return <main className="container judge">
  <section className="judgehero card"><div><div className="eyebrow"><Presentation size={15}/> Judge Demo Mode</div><h1>One story. Five minutes. Zero confusion.</h1><p>Use this page as the control room for your hackathon presentation. Every button below maps to a real product flow.</p></div><button className="ghost small" onClick={load}><RefreshCw size={15}/> Refresh metrics</button></section>
  <section className="judgemetrics">{[['Users',summary?.users||0,Users],['Skills',summary?.skills||0,Sparkles],['Swaps',summary?.swaps||0,Zap],['Completed',summary?.completed_swaps||0,CheckCircle2],['Learning hours',summary?.learning_hours||0,Target]].map(([label,value,I])=><div className="card judgestat" key={label}><I size={18}/><span>{label}</span><strong>{loading?'…':value}</strong></div>)}</section>
  <section className="section"><div className="sectionhead"><div><h2>Live demo storyline</h2><p>Follow the same path during judging instead of jumping between random screens.</p></div><span className="match">{summary?.ai_provider||'AI'} enabled</span></div><div className="judgeflow">{STEPS.map(([num,title,desc,path,I],idx)=><div className="card judgestep" key={num}><div className="stepnum">{num}</div><I size={22}/><h3>{title}</h3><p>{desc}</p><Link className="button small" to={path}>Open <ArrowRight size={14}/></Link>{idx<STEPS.length-1&&<span className="flowarrow">→</span>}</div>)}</div></section>
  <section className="section"><div className="sectionhead"><div><h2>Demo accounts</h2><p>Use separate browser windows to show both sides of an exchange.</p></div></div><div className="grid two">{(summary?.demo_accounts||[]).map(a=><div className="card demoaccount" key={a.email}><div className="avatar">{a.email[0].toUpperCase()}</div><div><strong>{a.email}</strong><span>Password: <b>{a.password}</b></span><small>{a.story}</small></div></div>)}</div></section>
  <section className="section"><div className="card judgepitch"><div className="eyebrow"><Sparkles size={14}/> Closing line</div><h2>“We don't just match people. We turn knowledge into measurable peer learning.”</h2><p>AI discovers complementary skills, the platform creates a trusted exchange, and every completed session becomes measurable community impact.</p></div></section>
 </main>
}
