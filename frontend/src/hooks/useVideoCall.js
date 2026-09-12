import {useCallback,useEffect,useRef,useState} from 'react';
import {useRealtime} from '../context/RealtimeContext';
import api,{errorMessage} from '../services/api';

export default function useVideoCall(sessionId){
  const {status,subscribe,send}=useRealtime();
  const [localStream,setLocalStream]=useState(null),[remoteStream,setRemoteStream]=useState(null);
  const [connection,setConnection]=useState('preview'),[error,setError]=useState(''),[preparing,setPreparing]=useState(false);
  const [mic,setMic]=useState(true),[camera,setCamera]=useState(true),[joined,setJoined]=useState(false);
  const stream=useRef(null),peer=useRef(null),candidates=useRef([]),config=useRef(null),desired=useRef(false),alive=useRef(true),generation=useRef(0),mediaBusy=useRef(false);
  const resetPeer=useCallback(()=>{
    generation.current++;candidates.current=[];
    if(peer.current){peer.current.ontrack=null;peer.current.onicecandidate=null;peer.current.onconnectionstatechange=null;peer.current.close();peer.current=null;}
    if(alive.current)setRemoteStream(null);
  },[]);
  const release=useCallback(()=>{
    desired.current=false;send({type:'call.leave'});resetPeer();
    stream.current?.getTracks().forEach(track=>track.stop());stream.current=null;
    if(alive.current){setLocalStream(null);setJoined(false);}
  },[send,resetPeer]);
  useEffect(()=>{
    alive.current=true;setLocalStream(null);setJoined(false);setConnection('preview');setError('');
    return()=>{alive.current=false;release();};
  },[release,sessionId]);
  const preview=async()=>{
    if(stream.current)return stream.current;
    if(mediaBusy.current)return null;
    const current=generation.current;
    mediaBusy.current=true;setPreparing(true);setError('');
    try{
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Use HTTPS or localhost to enable your camera and microphone.');
      let media;
      try{media=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1280},height:{ideal:720},facingMode:'user'},audio:{echoCancellation:true,noiseSuppression:true}});}
      catch(e){if(e.name!=='NotFoundError'&&e.name!=='OverconstrainedError')throw e;media=await navigator.mediaDevices.getUserMedia({video:false,audio:true});}
      if(!alive.current||current!==generation.current){media.getTracks().forEach(track=>track.stop());return null;}
      stream.current=media;setLocalStream(media);setMic(true);setCamera(media.getVideoTracks().length>0);
      return media;
    }catch(e){if(alive.current)setError(e.name==='NotAllowedError'?'Camera or microphone permission was denied. Allow access in your browser settings and try again.':e.message||'Could not access your camera or microphone.');return null;}
    finally{mediaBusy.current=false;if(alive.current)setPreparing(false);}
  };
  const makePeer=useCallback(()=>{
    const pc=new RTCPeerConnection(config.current);peer.current=pc;
    stream.current?.getTracks().forEach(track=>pc.addTrack(track,stream.current));
    pc.onicecandidate=event=>{if(event.candidate&&desired.current)send({type:'call.ice',session_id:sessionId,candidate:event.candidate.toJSON()});};
    pc.ontrack=event=>{if(alive.current)setRemoteStream(event.streams[0]||new MediaStream([event.track]));};
    pc.onconnectionstatechange=()=>{
      if(!alive.current||peer.current!==pc)return;
      setConnection(pc.connectionState);
      if(pc.connectionState==='connected')setError('');
      if(pc.connectionState==='failed')setError('The call could not connect across these networks. Try reconnecting or a different network.');
    };
    return pc;
  },[send,sessionId]);
  useEffect(()=>{
    let chain=Promise.resolve(),stopped=false;
    const handle=async event=>{
      if(stopped||!alive.current)return;
      if(event.type==='error'&&event.request_type?.startsWith('call.')){
        desired.current=false;resetPeer();setJoined(false);setConnection('preview');setError(event.message);return;
      }
      if(event.session_id!==sessionId||!desired.current)return;
      if(event.type==='call.closed'){release();setConnection('ended');setError(event.message);return;}
      if(event.type==='call.waiting'||event.type==='call.peer_left'){resetPeer();setConnection('waiting');return;}
      if(event.type==='call.joined'){setJoined(true);setConnection('waiting');return;}
      if(event.type==='call.peer_ready'){
        resetPeer();setConnection('connecting');const pc=makePeer();const current=generation.current;
        if(event.initiator){const offer=await pc.createOffer();if(stopped||current!==generation.current)return;await pc.setLocalDescription(offer);if(current===generation.current)send({type:'call.offer',session_id:sessionId,description:{type:pc.localDescription.type,sdp:pc.localDescription.sdp}});}
        return;
      }
      const pc=peer.current;
      if(event.type==='call.ice'){
        if(pc?.remoteDescription)await pc.addIceCandidate(event.candidate);else candidates.current.push(event.candidate);
      }else if(event.type==='call.offer'||event.type==='call.answer'){
        if(!pc)return;
        const current=generation.current;
        await pc.setRemoteDescription(event.description);
        if(stopped||current!==generation.current)return;
        for(const candidate of candidates.current)await pc.addIceCandidate(candidate);
        candidates.current=[];
        if(event.type==='call.offer'){
          await pc.setLocalDescription(await pc.createAnswer());
          if(current===generation.current)send({type:'call.answer',session_id:sessionId,description:{type:pc.localDescription.type,sdp:pc.localDescription.sdp}});
        }
      }
    };
    const unsubscribe=subscribe(event=>{
      chain=chain.then(()=>handle(event)).catch(()=>{if(!stopped&&alive.current&&desired.current){setConnection('failed');setError('We lost the call connection. Reconnect to try again.');}});
    });
    return()=>{stopped=true;unsubscribe();};
  },[subscribe,sessionId,send,resetPeer,makePeer,release]);
  useEffect(()=>{
    if(!desired.current)return;
    resetPeer();
    if(status==='connected'){setConnection('connecting');send({type:'call.join',session_id:sessionId});}
    else setConnection('reconnecting');
  },[status,send,sessionId,resetPeer]);
  const join=async()=>{
    const current=generation.current;
    setError('');
    if(status!=='connected'){setError('Waiting for a secure connection. Please try again in a moment.');return;}
    try{
      config.current=(await api.get(`/sessions/${sessionId}/ice-config`)).data;
      if(!alive.current||current!==generation.current)return;
      const media=await preview();if(!media||!alive.current||current!==generation.current)return;
      desired.current=true;setJoined(true);setConnection('connecting');
      if(!send({type:'call.join',session_id:sessionId})){desired.current=false;setJoined(false);setConnection('preview');setError('Connection interrupted. Please try joining again.');}
    }catch(e){setError(errorMessage(e,'Could not open the call room.'));}
  };
  const reconnect=()=>{send({type:'call.leave'});resetPeer();setConnection('connecting');send({type:'call.join',session_id:sessionId});};
  const toggleMic=()=>{stream.current?.getAudioTracks().forEach(track=>{track.enabled=!mic;});setMic(!mic);};
  const toggleCamera=()=>{stream.current?.getVideoTracks().forEach(track=>{track.enabled=!camera;});setCamera(!camera);};
  const leave=()=>{release();setConnection('ended');setError('');};
  return {localStream,remoteStream,connection,error,preparing,mic,camera,joined,preview,join,leave,reconnect,toggleMic,toggleCamera,status};
}
