import {useCallback,useEffect,useRef,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {ArrowRight,CalendarDays,CheckCircle2,Clock3,Globe2,MessageCircle,RefreshCw,Sparkles,Video,X} from 'lucide-react';
import api,{errorMessage} from '../services/api';
import {useAuth} from '../context/AuthContext';
import {useRealtime} from '../context/RealtimeContext';
import {asDate,dateTime,localInput,timeZone} from '../services/dates';
import Modal from '../components/Modal';
import {SkeletonSession} from '../components/Skeleton';

const blankForm={swap_id:'',participant_id:'',topic:'',date:'',time:'',duration_minutes:60};
const endTime=s=>asDate(s.scheduled_at).getTime()+s.duration_minutes*60000;

export default function Sessions(){
  const {user}=useAuth(),{subscribe}=useRealtime(),[params]=useSearchParams();
  const [rows,setRows]=useState([]),[partners,setPartners]=useState([]),[form,setForm]=useState(blankForm);
  const [loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(''),[success,setSuccess]=useState('');
  const [tab,setTab]=useState('upcoming'),[editing,setEditing]=useState(null),[confirm,setConfirm]=useState(null),[now,setNow]=useState(Date.now());
  const formRef=useRef(null),topicRef=useRef(null);
  const load=useCallback(async()=>{
    try{const [a,b]=await Promise.all([api.get('/sessions'),api.get('/partners')]);setRows(a.data);setPartners(b.data);}
    catch(e){setError(errorMessage(e,'Could not load your learning schedule.'));}
    finally{setLoading(false);}
  },[]);
  useEffect(()=>{load();const timer=setInterval(()=>setNow(Date.now()),30000);return()=>clearInterval(timer);},[load]);
  useEffect(()=>subscribe(event=>{if(['ready','session.updated','swaps.changed'].includes(event.type))load();}),[subscribe,load]);
  useEffect(()=>{
    if(editing)return;
    const match=partners.find(p=>String(p.swap_id)===params.get('swap'))||partners.find(p=>String(p.partner.id)===params.get('user'));
    if(match)setForm(current=>current.swap_id?current:{...current,swap_id:String(match.swap_id),participant_id:String(match.partner.id),topic:match.topics[0]});
  },[partners,params,editing]);
  const set=(key,value)=>{setSuccess('');setForm(current=>({...current,[key]:value}));};
  const choosePartner=value=>{
    const p=partners.find(x=>String(x.swap_id)===value);
    setForm(current=>({...current,swap_id:value,participant_id:p?String(p.partner.id):'',topic:p?.topics[0]||''}));
  };
  const stopEditing=()=>{setEditing(null);setForm(blankForm);};
  const reschedule=s=>{
    const local=localInput(s.scheduled_at);setEditing(s);setError('');setSuccess('');
    setForm({swap_id:String(s.swap_id||''),participant_id:String(s.organizer.id===user.id?s.participant.id:s.organizer.id),topic:s.topic,date:local.slice(0,10),time:local.slice(11,16),duration_minutes:s.duration_minutes});
    formRef.current?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});
    topicRef.current?.focus({preventScroll:true});
  };
  const partnerName=editing?(editing.organizer.id===user.id?editing.participant.name:editing.organizer.name):partners.find(p=>String(p.swap_id)===form.swap_id)?.partner.full_name;
  const start=form.date&&form.time?new Date(`${form.date}T${form.time}`):null;
  const submit=e=>{
    e.preventDefault();setError('');setSuccess('');
    if(!start||!Number.isFinite(start.getTime())||start.getTime()<=Date.now()){setError('Choose a date and time in the future.');return;}
    if(form.topic.trim().length<2){setError('Add a topic with at least two characters.');return;}
    setConfirm({type:'book'});
  };
  const apply=async()=>{
    if(busy)return;setBusy(true);setError('');
    try{
      if(confirm.type==='book'){
        const values={topic:form.topic.trim(),scheduled_at:start.toISOString(),duration_minutes:Number(form.duration_minutes)};
        if(editing)await api.patch(`/sessions/${editing.id}`,values);
        else await api.post('/sessions',{...values,participant_id:Number(form.participant_id),swap_id:Number(form.swap_id)});
        setSuccess(editing?'Session rescheduled. Your partner has been notified.':'You’re booked! Your partner can find the session in their schedule.');
        stopEditing();setTab('upcoming');
      }else{
        await api.patch(`/sessions/${confirm.session.id}`,{status:confirm.type});
        setSuccess(confirm.type==='completed'?'Session completed. Head to your swaps to leave a review.':'Session cancelled. Your partner has been notified.');
        if(confirm.type==='completed')setTab('past');
      }
      setConfirm(null);await load();
    }catch(e){setError(errorMessage(e,'We could not save that change. Please try again.'));setConfirm(null);}
    finally{setBusy(false);}
  };
  const upcoming=rows.filter(s=>s.status==='scheduled'&&endTime(s)>now).sort((a,b)=>asDate(a.scheduled_at)-asDate(b.scheduled_at));
  const past=rows.filter(s=>s.status==='completed'||(s.status==='scheduled'&&endTime(s)<=now)).sort((a,b)=>asDate(b.scheduled_at)-asDate(a.scheduled_at));
  const cancelled=rows.filter(s=>s.status==='cancelled');
  const visible={upcoming,past,cancelled}[tab],next=upcoming[0];
  return <main className="container workspace-page sessions-page page-transition">
    <div className="pageintro"><div><div className="eyebrow"><CalendarDays size={15}/> Time well shared</div><h1>Make room for your next skill.</h1><p>A little time, a good partner, and something new to learn.</p></div><span className="timezone-label"><Globe2 size={15}/>{timeZone.replaceAll('_',' ')}</span></div>
    {error&&<div className="errorbox card" role="alert"><span>{error}</span><button className="ghost small" onClick={()=>{setError('');load();}}><RefreshCw size={14}/> Refresh</button></div>}
    {success&&<div className="successbox" role="status"><CheckCircle2 size={18}/><span>{success}</span></div>}
    <div className="schedule-summary"><div className="schedule-highlight"><span className="section-kicker">{next?'Next on your calendar':'Your next chapter'}</span><h2>{next?.topic||'A new skill starts with a date.'}</h2><p>{next?dateTime(next.scheduled_at):'Book a focused session with an exchange partner.'}</p><span className="summary-decoration" aria-hidden="true"><CalendarDays size={60}/></span></div><div className="schedule-stat"><CalendarDays size={20}/><strong>{loading?'—':upcoming.length}</strong><span>Upcoming sessions</span></div><div className="schedule-stat"><Sparkles size={20}/><strong>{loading?'—':Math.round(rows.filter(s=>s.status==='completed').reduce((sum,s)=>sum+s.duration_minutes,0)/6)/10}<small>h</small></strong><span>Time spent learning</span></div></div>
    <div className="booking-layout"><form ref={formRef} className="card booking-form form" onSubmit={submit}>
      <div className="booking-form-title"><span className="booking-icon"><CalendarDays size={22}/></span><div><h2>{editing?'Find a new time':'Plan a session'}</h2><p>{editing?'Keep the topic. Make the time work.':'Your next learning moment, all in one place.'}</p></div></div>
      {editing?<div className="editing-partner"><span className="avatar">{partnerName?.[0]}</span><div><small>Learning with</small><strong>{partnerName}</strong></div><button type="button" className="ghost icon-button" aria-label="Stop rescheduling" onClick={stopEditing}><X size={17}/></button></div>:<label className="field"><span>Exchange partner</span><select required value={form.swap_id} disabled={loading||!partners.length} onChange={e=>choosePartner(e.target.value)}><option value="">Choose an accepted exchange</option>{partners.map(p=><option key={p.swap_id} value={p.swap_id}>{p.partner.full_name} · {p.topics[0]} (#{p.swap_id})</option>)}</select></label>}
      {!loading&&!partners.length&&!editing&&<div className="booking-note">Accept a swap to unlock sessions with your partner. <Link to="/swaps">View exchanges <ArrowRight size={13}/></Link></div>}
      <label className="field"><span>What will you learn?</span><input ref={topicRef} required minLength={2} maxLength={180} list="session-topics" value={form.topic} placeholder="e.g. A first look at React hooks" onChange={e=>set('topic',e.target.value)}/><datalist id="session-topics">{(partners.find(p=>String(p.swap_id)===form.swap_id)?.topics||[]).map(topic=><option key={topic} value={topic}/>)}</datalist></label>
      <div className="booking-date-time"><label className="field"><span>Date</span><input required type="date" min={localInput().slice(0,10)} value={form.date} onChange={e=>set('date',e.target.value)}/></label><label className="field"><span>Time</span><input required type="time" value={form.time} onChange={e=>set('time',e.target.value)}/></label></div>
      <fieldset className="duration-field"><legend>How long do you need?</legend><div>{[30,60,90].map(minutes=><label className={Number(form.duration_minutes)===minutes?'selected':''} key={minutes}><input type="radio" name="duration" value={minutes} checked={Number(form.duration_minutes)===minutes} onChange={()=>set('duration_minutes',minutes)}/><span>{minutes}<small>min</small></span></label>)}</div></fieldset>
      <div className="included-video"><Video size={19}/><div><strong>Your call room is included</strong><small>Join here, with no extra app or meeting link.</small></div></div>
      <button className="button full" disabled={busy||loading||(!editing&&!partners.length)}>{editing?'Review new time':'Review booking'} <ArrowRight size={16}/></button><p className="booking-footnote">Times are shown in your local time zone.</p>
    </form>
    <section className="schedule-list"><div className="schedule-list-heading"><h2>Your learning sessions</h2><button className="ghost icon-button" aria-label="Refresh sessions" onClick={load}><RefreshCw size={16}/></button></div><div className="session-tabs" aria-label="Filter sessions">{[['upcoming','Upcoming',upcoming.length],['past','Past',past.length],['cancelled','Cancelled',cancelled.length]].map(([key,label,count])=><button key={key} aria-pressed={tab===key} className={tab===key?'active':''} onClick={()=>setTab(key)}>{label}<span>{count}</span></button>)}</div>
      {loading?<div className="stack">{Array.from({length:3},(_,i)=><SkeletonSession key={i}/>)}</div>:visible.length?<div className="stack">{visible.map(s=>{
        const partner=s.organizer.id===user.id?s.participant:s.organizer;
        const started=asDate(s.scheduled_at).getTime()<=now;
        const joinable=s.status==='scheduled'&&asDate(s.call_opens_at).getTime()<=now&&endTime(s)+3600000>=now;
        const date=asDate(s.scheduled_at);
        return <article className="card booking-card" key={s.id}><div className="booking-card-main"><div className="session-date"><span>{date.toLocaleDateString(undefined,{month:'short'})}</span><strong>{date.getDate()}</strong><small>{date.toLocaleDateString(undefined,{weekday:'short'})}</small></div><div className="session-detail"><div className="session-labels"><span className={`status ${s.status}`}>{s.status==='scheduled'?(endTime(s)<=now?'Awaiting completion':'Booked'):s.status}</span><span><Clock3 size={13}/>{s.duration_minutes} min</span></div><h3>{s.topic}</h3><p>with <strong>{partner.name}</strong></p><time dateTime={s.scheduled_at}>{date.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'})} · {timeZone.replaceAll('_',' ')}</time></div></div><div className="booking-card-actions">
          {s.status==='scheduled'&&<>{joinable?<Link className="button small" to={`/sessions/${s.id}/call`}><Video size={15}/> Join session</Link>:<span className="call-availability">{endTime(s)<=now?'Ready to reflect on your session?':'Call opens 15 min before'}</span>}{started&&<button className="ghost small" disabled={busy} onClick={()=>setConfirm({type:'completed',session:s})}><CheckCircle2 size={15}/> Complete</button>}<button className="ghost small" disabled={busy} onClick={()=>reschedule(s)}>Reschedule</button><button className="ghost small cancel-session" disabled={busy} onClick={()=>setConfirm({type:'cancelled',session:s})}>Cancel</button></>}
          {s.status==='completed'&&s.swap_id&&<Link className="button secondary small" to={`/swaps?review=${s.swap_id}`}>Review exchange <ArrowRight size={14}/></Link>}
          <Link className="ghost icon-button" aria-label={`Message ${partner.name}`} to={`/messages/${partner.id}`}><MessageCircle size={17}/></Link>
        </div></article>;
      })}</div>:<div className="card schedule-empty"><span className="welcome-icon"><CalendarDays size={30}/></span><h3>{tab==='upcoming'?'Make your next connection count.':tab==='past'?'Your progress will live here.':'A little flexibility goes a long way.'}</h3><p>{tab==='upcoming'?'Choose a partner and book some time to learn together.':tab==='past'?'Completed sessions become part of your learning story.':'Cancelled sessions will appear here.'}</p></div>}
    </section></div>
    {confirm&&<Modal title={confirm.type==='book'?(editing?'Confirm your new time':'Your next learning moment'):confirm.type==='completed'?'Wrap up this session?':'Cancel this session?'} busy={busy} onClose={()=>setConfirm(null)}>
      {confirm.type==='book'?<><p className="dialog-intro">A focused session with {partnerName}. We’ll notify your partner when you confirm.</p><div className="booking-review"><strong>{form.topic}</strong><span><CalendarDays size={17}/>{start?.toLocaleString(undefined,{dateStyle:'full',timeStyle:'short'})}</span><span><Clock3 size={17}/>{form.duration_minutes} minutes</span><span><Video size={17}/>Private SkillSwap video room</span><small>{timeZone}</small></div></>:<p className="dialog-intro">{confirm.type==='completed'?`Mark “${confirm.session.topic}” as completed and add it to your learning history.`:`Your partner will be notified that “${confirm.session.topic}” is cancelled. You can book a new session whenever you’re ready.`}</p>}
      <div className="dialog-actions"><button className="ghost" disabled={busy} onClick={()=>setConfirm(null)}>Go back</button><button className={confirm.type==='cancelled'?'danger':'button'} disabled={busy} onClick={apply}>{busy?'Saving…':confirm.type==='book'?'Confirm booking':confirm.type==='completed'?'Complete session':'Cancel session'}</button></div>
    </Modal>}
  </main>;
}
