import {useCallback,useEffect,useRef,useState} from 'react';
import {Link,useParams,useNavigate} from 'react-router-dom';
import {ArrowLeft,CalendarDays,Check,CheckCheck,MessageCircle,Search,Send,ShieldCheck,RefreshCw} from 'lucide-react';
import api,{errorMessage} from '../services/api';
import {useAuth} from '../context/AuthContext';
import {useRealtime} from '../context/RealtimeContext';
import {asDate,dateTime,timeOnly} from '../services/dates';
import {SkeletonThread} from '../components/Skeleton';

function mergeMessages(current,incoming){return [...new Map([...current,...incoming].map(m=>[m.id,m])).values()].sort((a,b)=>a.id-b.id);}

export default function Messages(){
  const {otherId}=useParams(),{user}=useAuth(),{status,subscribe}=useRealtime(),navigate=useNavigate();
  const [conversations,setConversations]=useState([]),[partners,setPartners]=useState([]),[messages,setMessages]=useState([]);
  const [loading,setLoading]=useState(true),[chatLoading,setChatLoading]=useState(false),[error,setError]=useState('');
  const [search,setSearch]=useState(''),[body,setBody]=useState(''),[outbox,setOutbox]=useState([]),[older,setOlder]=useState(false),[historyLoading,setHistoryLoading]=useState(false);
  const scroll=useRef(null),pinned=useRef(true),readThrough=useRef({}),drafts=useRef({}),active=useRef(otherId);
  active.current=otherId;
  const conversation=conversations.find(c=>String(c.partner.id)===otherId);
  const partner=conversation?.partner||partners.find(p=>String(p.partner.id)===otherId)?.partner;
  const reload=useCallback(async()=>{
    try{const [a,b]=await Promise.all([api.get('/conversations'),api.get('/partners')]);setConversations(a.data);setPartners(b.data);}
    catch(e){setError(errorMessage(e,'Could not load your conversations.'));}
    finally{setLoading(false);}
  },[]);
  useEffect(()=>{reload();},[reload]);
  const markRead=useCallback(()=>{
    if(!conversation||document.hidden||!document.hasFocus())return;
    const last=messages.filter(m=>m.receiver_id===user.id).at(-1)?.id;
    if(!last||readThrough.current[conversation.id]>=last)return;
    readThrough.current[conversation.id]=last;
    api.post(`/conversations/${conversation.id}/read`,{through_id:last}).then(()=>{
      setConversations(rows=>rows.map(c=>c.id===conversation.id?{...c,unread_count:0}:c));
    }).catch(()=>{delete readThrough.current[conversation.id];});
  },[conversation?.id,messages,user.id]);
  useEffect(()=>{
    markRead();window.addEventListener('focus',markRead);document.addEventListener('visibilitychange',markRead);
    return()=>{window.removeEventListener('focus',markRead);document.removeEventListener('visibilitychange',markRead);};
  },[markRead]);
  useEffect(()=>{
    setMessages([]);setError('');setOlder(false);setBody(drafts.current[otherId]||'');pinned.current=true;
    if(!otherId)return;
    if(!/^\d+$/.test(otherId)||Number(otherId)===user.id){setError('Choose a conversation with another member.');return;}
    const controller=new AbortController();setChatLoading(true);
    (async()=>{
      try{
        await api.post('/conversations',{participant_id:Number(otherId)},{signal:controller.signal});
        const response=await api.get(`/messages/${otherId}`,{params:{limit:50},signal:controller.signal});
        if(controller.signal.aborted)return;
        setMessages(current=>mergeMessages(response.data,current));setOlder(response.data.length===50);reload();
      }catch(e){if(!controller.signal.aborted)setError(errorMessage(e,'Could not open this conversation.'));}
      finally{if(!controller.signal.aborted)setChatLoading(false);}
    })();
    return()=>controller.abort();
  },[otherId,user.id,reload]);
  useEffect(()=>subscribe(event=>{
    if(event.type==='ready'){
      reload();
      if(otherId)api.get(`/messages/${otherId}`,{params:{limit:100}}).then(r=>{if(active.current===otherId)setMessages(current=>mergeMessages(current,r.data));}).catch(()=>{});
    }
    if(['conversations.changed','swaps.changed','messages.read'].includes(event.type))reload();
    if(event.type==='message.created'){
      const m=event.message;reload();
      if([m.sender_id,m.receiver_id].includes(Number(otherId))){
        setMessages(current=>mergeMessages(current,[m]));
        setOutbox(current=>current.filter(x=>x.client_id!==m.client_id));
      }
    }
    if(event.type==='messages.read'&&event.conversation_id===conversation?.id){
      setMessages(current=>current.map(m=>m.receiver_id===event.reader_id&&m.id<=event.through_id?{...m,read_at:event.read_at}:m));
    }
  }),[subscribe,otherId,reload,conversation?.id]);
  useEffect(()=>{if(pinned.current&&scroll.current)scroll.current.scrollTop=scroll.current.scrollHeight;},[messages,outbox,chatLoading]);
  const deliver=async entry=>{
    setOutbox(rows=>rows.map(m=>m.client_id===entry.client_id?{...m,status:'sending'}:m));
    try{
      const response=await api.post('/messages',{receiver_id:entry.receiver_id,body:entry.body,client_id:entry.client_id});
      if(active.current===String(entry.receiver_id))setMessages(current=>mergeMessages(current,[response.data]));
      setOutbox(rows=>rows.filter(m=>m.client_id!==entry.client_id));reload();
    }catch(e){setOutbox(rows=>rows.map(m=>m.client_id===entry.client_id?{...m,status:'failed',error:errorMessage(e,'Message not sent. Check your connection and retry.')}:m));}
  };
  const send=event=>{
    event.preventDefault();if(!body.trim()||!conversation)return;
    const entry={client_id:crypto.randomUUID(),receiver_id:Number(otherId),body:body.trim(),status:'sending'};
    setOutbox(rows=>[...rows,entry]);setBody('');drafts.current[otherId]='';pinned.current=true;deliver(entry);
  };
  const loadOlder=async()=>{
    if(!messages.length||historyLoading)return;
    const chatId=otherId;setHistoryLoading(true);const height=scroll.current?.scrollHeight||0;
    try{const r=await api.get(`/messages/${chatId}`,{params:{limit:50,before_id:messages[0].id}});
      if(active.current!==chatId)return;
      pinned.current=false;setMessages(current=>mergeMessages(r.data,current));setOlder(r.data.length===50);
      requestAnimationFrame(()=>{if(scroll.current)scroll.current.scrollTop=scroll.current.scrollHeight-height;});
    }catch(e){setError(errorMessage(e));}finally{setHistoryLoading(false);}
  };
  const filtered=conversations.filter(c=>c.partner.full_name.toLowerCase().includes(search.toLowerCase()));
  const newPartners=partners.filter((p,i,all)=>!conversations.some(c=>c.partner.id===p.partner.id)&&all.findIndex(x=>x.partner.id===p.partner.id)===i);
  return <main className="container workspace-page messages-page page-transition">
    <div className="pageintro"><div><div className="eyebrow"><MessageCircle size={15}/> Your learning circle</div><h1>Good things start with hello.</h1><p>Plan the next step, share an idea, and keep learning together.</p></div><span className={`connection-pill ${status}`} role="status"><i/>{status==='connected'?'Live connection':status==='unavailable'?'Live connection unavailable':'Reconnecting…'}</span></div>
    {error&&<div className="errorbox card" role="alert"><span>{error}</span><button className="ghost small" onClick={reload}><RefreshCw size={14}/> Retry</button></div>}
    <div className={`inbox-layout card ${otherId?'has-chat':''}`}>
      <aside className="inbox-sidebar"><div className="inbox-title"><h2>Messages</h2><span>{conversations.length}</span></div><label className="inbox-search"><Search size={16}/><input aria-label="Search conversations" placeholder="Find a conversation" value={search} onChange={e=>setSearch(e.target.value)}/></label>
        <div className="inbox-threads">{loading?<>{Array.from({length:5},(_,i)=><SkeletonThread key={i}/>)}</>:filtered.map(c=><Link className={`thread ${String(c.partner.id)===otherId?'selected':''}`} to={`/messages/${c.partner.id}`} key={c.id}><span className="avatar">{c.partner.full_name[0]}</span><span className="thread-copy"><strong>{c.partner.full_name}</strong><small>{c.last_message?.body||'Your exchange starts here'}</small></span><span className="thread-meta">{c.last_message&&<time>{timeOnly(c.last_message.created_at)}</time>}{c.unread_count>0&&<b aria-label={`${c.unread_count} unread messages`}>{c.unread_count}</b>}</span></Link>)}
          {!loading&&!filtered.length&&<div className="inbox-empty"><MessageCircle size={24}/><p>{search?'No matching conversations.':'Your next hello is waiting.'}</p>{!search&&<Link to="/swaps">Visit your exchanges →</Link>}</div>}
          {!!newPartners.length&&!search&&<div className="partner-suggestions"><span className="section-kicker">Ready to connect</span>{newPartners.map(p=><Link className="thread" to={`/messages/${p.partner.id}`} key={p.partner.id}><span className="avatar">{p.partner.full_name[0]}</span><span className="thread-copy"><strong>{p.partner.full_name}</strong><small>Accepted exchange · Say hello</small></span></Link>)}</div>}
        </div><div className="inbox-privacy"><ShieldCheck size={15}/> Just you and your exchange partner</div>
      </aside>
      <section className="inbox-chat" aria-label="Conversation">{otherId?<>
        <header className="chat-header"><button className="ghost icon-button mobile-chat-back" aria-label="Back to conversations" onClick={()=>navigate('/messages')}><ArrowLeft size={20}/></button><span className="avatar">{partner?.full_name?.[0]||'?'}</span><div className="chat-person"><strong>{partner?.full_name||'Conversation'}</strong><small>Your shared space to make progress</small></div>{conversation&&<Link className="button secondary small" to={`/sessions?user=${otherId}`}><CalendarDays size={15}/><span>Schedule</span></Link>}</header>
        <div className="chat-scroll" ref={scroll} onScroll={()=>{const el=scroll.current;pinned.current=el.scrollHeight-el.scrollTop-el.clientHeight<100;}}>
          {chatLoading?<div className="loading" role="status">Loading conversation…</div>:<>
            {older&&<button className="ghost small history-button" disabled={historyLoading} onClick={loadOlder}>{historyLoading?'Loading…':'Load earlier messages'}</button>}
            {!messages.length&&<div className="chat-welcome"><span className="welcome-icon"><MessageCircle size={27}/></span><h3>A small hello. A new possibility.</h3><p>Introduce yourself and share what you’d love to learn.</p></div>}
            {messages.map((m,i)=><div key={m.id}>{(!i||asDate(m.created_at).toDateString()!==asDate(messages[i-1].created_at).toDateString())&&<div className="message-day">{asDate(m.created_at).toLocaleDateString(undefined,{month:'long',day:'numeric'})}</div>}<div className={`message-row ${m.sender_id===user.id?'own':''}`}><div className="message-bubble"><p>{m.body}</p><div className="message-time"><time dateTime={m.created_at} title={dateTime(m.created_at)}>{timeOnly(m.created_at)}</time>{m.sender_id===user.id&&(m.read_at?<CheckCheck size={13} aria-label="Read"/>:<Check size={13} aria-label="Delivered"/>)}</div></div></div></div>)}
            {outbox.filter(m=>m.receiver_id===Number(otherId)).map(m=><div className="message-row own" key={m.client_id}><div className={`message-bubble ${m.status==='failed'?'failed':'pending'}`}><p>{m.body}</p>{m.status==='failed'?<div className="message-retry" role="alert"><span>{m.error}</span><button onClick={()=>deliver(m)}>Retry send</button></div>:<small>Sending…</small>}</div></div>)}
          </>}
        </div>
        <form className="message-composer" onSubmit={send}><textarea rows={2} aria-label="Your message" maxLength={2000} placeholder="Write something thoughtful…" value={body} disabled={!conversation||chatLoading} onChange={e=>{setBody(e.target.value);drafts.current[otherId]=e.target.value;}} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();send(e);}}}/><button className="button send-button" aria-label="Send message" disabled={!body.trim()||!conversation||chatLoading}><Send size={18}/></button></form><div className="composer-hint"><span>Enter to send · Shift + Enter for a new line</span><span>{body.length}/2000</span></div>
      </>:<div className="chat-welcome full-welcome"><span className="welcome-icon"><MessageCircle size={36}/></span><span className="section-kicker">Stay connected</span><h2>One conversation.<br/>So much to learn.</h2><p>Choose an exchange partner to start chatting.<br/>Your next session starts right here.</p><Link className="button secondary" to="/swaps">View your exchanges <ArrowLeft className="rotate-arrow" size={16}/></Link></div>}</section>
    </div>
  </main>;
}
