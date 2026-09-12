import {useEffect,useRef,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {ArrowLeft,Camera,CameraOff,CheckCircle2,Clock3,Headphones,Mic,MicOff,PhoneOff,RefreshCw,ShieldCheck,Video} from 'lucide-react';
import api,{errorMessage} from '../services/api';
import {useAuth} from '../context/AuthContext';
import {dateTime} from '../services/dates';
import useVideoCall from '../hooks/useVideoCall';

function VideoTile({stream,muted=false,className='',label,camera=true}){
  const ref=useRef(null),[playBlocked,setPlayBlocked]=useState(false);
  useEffect(()=>{
    const video=ref.current;video.srcObject=stream;
    if(stream)video.play().catch(()=>setPlayBlocked(true));
    return()=>{video.srcObject=null;};
  },[stream]);
  return <div className={`video-tile ${className}`}><video ref={ref} autoPlay playsInline muted={muted} className={!camera?'video-hidden':''}/>{(!stream||!camera)&&<div className="video-avatar"><span>{label?.[0]||'S'}</span><small>{!camera?'Camera is off':'Your camera preview'}</small></div>}<div className="video-label">{muted&&<ShieldCheck size={13}/>} {label}</div>{playBlocked&&<button className="button video-play" onClick={()=>ref.current.play().then(()=>setPlayBlocked(false))}>Play video and audio</button>}</div>;
}

export default function VideoSession(){
  const {sessionId}=useParams(),{user}=useAuth();
  const [session,setSession]=useState(null),[loadError,setLoadError]=useState(''),[joining,setJoining]=useState(false);
  const call=useVideoCall(Number(sessionId));
  useEffect(()=>{const controller=new AbortController();setSession(null);setLoadError('');api.get(`/sessions/${sessionId}`,{signal:controller.signal}).then(r=>setSession(r.data)).catch(e=>{if(!controller.signal.aborted)setLoadError(errorMessage(e,'Could not open this session.'));});return()=>controller.abort();},[sessionId]);
  if(loadError)return <main className="container narrow"><div className="card schedule-empty" role="alert"><ShieldCheck size={30}/><h2>This room is unavailable.</h2><p>{loadError}</p><Link className="button" to="/sessions">Back to sessions</Link></div></main>;
  if(!session)return <main className="container loading" role="status">Opening your private session…</main>;
  const partner=session.organizer.id===user.id?session.participant:session.organizer;
  const labels={preview:'Get comfortable',connecting:'Connecting your call…',waiting:`Waiting for ${partner.name}`,connected:'You’re connected',disconnected:'Connection interrupted',failed:'Connection needs attention',reconnecting:'Reconnecting to your session…',ended:'Time well shared'};
  const join=async()=>{setJoining(true);try{await call.join();}finally{setJoining(false);}};
  return <main className="container workspace-page call-page"><Link className="back" to="/sessions"><ArrowLeft size={16}/> Your sessions</Link><header className="call-heading"><div><div className="eyebrow"><Video size={15}/> Your learning room</div><h1>{session.topic}</h1><p>with {partner.name} <span>·</span> <Clock3 size={14}/> {session.duration_minutes} minutes</p></div><span className="call-private"><ShieldCheck size={16}/> Private, one-to-one session</span></header>
    {call.error&&<div className="errorbox card" role="alert"><span>{call.error}</span>{call.joined&&<button className="ghost small" onClick={call.reconnect}><RefreshCw size={15}/> Reconnect</button>}</div>}
    {call.connection==='ended'?<section className="card call-ended"><span className="welcome-icon"><CheckCircle2 size={36}/></span><div className="section-kicker">Keep the momentum</div><h2>A little wiser than before.</h2><p>Your camera and microphone are off. Complete your session and share a thoughtful review of your exchange.</p><div className="dialog-actions"><Link className="button" to="/sessions">Complete & reflect</Link>{session.status==='scheduled'&&<button className="ghost" disabled={joining} onClick={join}>Rejoin session</button>}</div></section>:
    <div className={`call-stage ${call.joined?'in-call':'in-preview'}`}>
      <section className="call-video-area">{call.joined?<>
        <VideoTile stream={call.remoteStream} label={partner.name} className="remote-tile"/>
        {!call.remoteStream&&<div className="waiting-partner"><span className="waiting-orbit"><Headphones size={35}/></span><h2>{labels[call.connection]||'Connecting…'}</h2><p>{call.connection==='waiting'?'Your partner can join this room from their Sessions page.':'Making a little room for a great conversation.'}</p>{['failed','disconnected'].includes(call.connection)&&<button className="button light-button" onClick={call.reconnect}><RefreshCw size={16}/> Reconnect call</button>}</div>}
        <VideoTile stream={call.localStream} muted label="You" camera={call.camera} className="self-tile"/>
      </>:<VideoTile stream={call.localStream} muted label="You · Preview" camera={call.camera} className="preview-tile"/>}
      <div className={`call-state ${call.connection}`} role="status"><i/>{labels[call.connection]||'Connecting…'}</div>
      <div className="call-controls"><button aria-label={call.mic?'Mute microphone':'Unmute microphone'} aria-pressed={!call.mic} className={!call.mic?'off':''} disabled={!call.localStream} onClick={call.toggleMic}>{call.mic?<Mic size={21}/>:<MicOff size={21}/>}</button><button aria-label={call.camera?'Turn camera off':'Turn camera on'} aria-pressed={!call.camera} className={!call.camera?'off':''} disabled={!call.localStream?.getVideoTracks().length} onClick={call.toggleCamera}>{call.camera?<Camera size={21}/>:<CameraOff size={21}/>}</button>{call.joined&&<button className="hangup" aria-label="Leave call" onClick={call.leave}><PhoneOff size={21}/><span>Leave</span></button>}</div>
    </section>
    {!call.joined&&<aside className="call-lobby"><span className="section-kicker">One person. A new perspective.</span><h2>Ready when<br/>you are.</h2><p>Check your camera and microphone, take a breath, and let the learning begin.</p><div className="call-session-info"><span className="avatar">{partner.name[0]}</span><div><strong>{partner.name}</strong><small>{dateTime(session.scheduled_at)}</small></div></div>{!call.localStream&&<button className="button secondary full" disabled={call.preparing||joining} onClick={call.preview}><Camera size={17}/>{call.preparing?'Opening camera…':'Check camera & microphone'}</button>}<button className="button full" disabled={joining||call.preparing||call.status!=='connected'||session.status!=='scheduled'} onClick={join}><Video size={18}/>{joining?'Joining…':'Join learning session'}</button><small className="lobby-note"><ShieldCheck size={14}/> Only you and your partner can enter. Calls open 15 minutes before your session.</small></aside>}
    </div>}
    <div className="call-bottom-note"><Headphones size={16}/><span>Headphones help keep your conversation clear. Your video is never recorded by SkillSwap.</span><Link to={`/messages/${partner.id}`}>Open conversation →</Link></div>
  </main>;
}
