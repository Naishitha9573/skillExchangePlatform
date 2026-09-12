import {useEffect,useState} from 'react';
import {Link,useParams,useNavigate} from 'react-router-dom';
import {ArrowLeft,Send,MapPin,Clock3,BrainCircuit,CalendarDays} from 'lucide-react';
import api,{errorMessage} from '../services/api';
import {useAuth} from '../context/AuthContext';
export default function SkillDetail(){
  const {id}=useParams(),navigate=useNavigate(),{user}=useAuth();
  const [skill,setSkill]=useState(null),[mine,setMine]=useState([]),[message,setMessage]=useState(''),[selected,setSelected]=useState('');
  const [done,setDone]=useState(false),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>{
    const controller=new AbortController();setLoading(true);setDone(false);setError('');
    Promise.all([api.get(`/skills/${id}`,{signal:controller.signal}),api.get('/skills/mine',{signal:controller.signal})]).then(([a,b])=>{setSkill(a.data);setMine(b.data.filter(x=>x.type==='Offering'));}).catch(e=>{if(!controller.signal.aborted)setError(errorMessage(e,'Could not load this opportunity.'));}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>controller.abort();
  },[id]);
  const submit=async event=>{
    event.preventDefault();if(!selected||busy)return;setBusy(true);setError('');
    try{await api.post('/swaps',{receiver_id:skill.owner_id,offered_skill_id:Number(selected),requested_skill_id:skill.id,message});setDone(true);}
    catch(e){setError(errorMessage(e,'Could not send your proposal. Please try again.'));}finally{setBusy(false);}
  };
  if(loading)return <main className="container loading" role="status">Loading opportunity…</main>;
  return <main className="container narrow"><button className="back" onClick={()=>navigate(-1)}><ArrowLeft size={17}/> Back</button>{error&&<div className="errorbox card" role="alert"><span>{error}</span></div>}{skill&&<><article className="detail card"><div className="cardtop"><span className={skill.type==='Offering'?'pill green':'pill blue'}>{skill.type}</span><span>{skill.category}</span></div><h1>{skill.title}</h1><p className="lead">{skill.description}</p><div className="detailmeta"><span><MapPin size={16}/>{skill.owner?.location||'Remote'}</span><span><Clock3 size={16}/>{skill.availability}</span><span>{skill.level}</span></div><div className="tags">{skill.tags.split(',').filter(Boolean).map(x=><span key={x}>#{x.trim()}</span>)}</div><div className="owner"><div className="avatar">{skill.owner?.full_name?.[0]}</div><div><strong>{skill.owner?.full_name}</strong><span>{skill.owner?.bio||'SkillSwap member'}</span></div></div></article>{skill.owner_id!==user.id&&<form className="card form swapform" onSubmit={submit}><div className="eyebrow"><BrainCircuit size={15}/> Propose a swap</div><h2>What can you teach in return?</h2>{mine.length?<label className="field"><span>Your offered skill</span><select required value={selected} onChange={e=>setSelected(e.target.value)}><option value="">Select one of your offered skills</option>{mine.map(x=><option value={x.id} key={x.id}>{x.title}</option>)}</select></label>:<p>Add something you can teach before proposing an exchange. <Link className="button small" to="/add-skill">Add a skill</Link></p>}<label className="field"><span>A friendly introduction</span><textarea rows={4} maxLength={2000} value={message} onChange={e=>setMessage(e.target.value)} placeholder="Share what you’d love to learn together…"/></label><button className="button full" disabled={done||busy||!mine.length}>{done?'Request sent':busy?'Sending…':<><Send size={16}/> Send swap request</>}</button>{done&&<div className="successbox" role="status"><CalendarDays size={16}/><span>Once your partner accepts, you can chat, book, and learn together. <Link to="/swaps"><b>View your swaps →</b></Link></span></div>}</form>}</>}</main>;
}
