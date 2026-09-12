import {createContext,useCallback,useContext,useEffect,useRef,useState} from 'react';
import {useAuth} from './AuthContext';
import api,{websocketUrl} from '../services/api';
const RealtimeContext=createContext(null);
export const useRealtime=()=>useContext(RealtimeContext);
export function RealtimeProvider({children}){
  const {user,logout}=useAuth();
  const [status,setStatus]=useState('offline'),[unread,setUnread]=useState(0);
  const socket=useRef(null),listeners=useRef(new Set());
  const subscribe=useCallback(fn=>{listeners.current.add(fn);return()=>listeners.current.delete(fn);},[]);
  const send=useCallback(event=>{if(socket.current?.readyState!==WebSocket.OPEN)return false;socket.current.send(JSON.stringify(event));return true;},[]);
  useEffect(()=>{
    if(!user){setStatus('offline');setUnread(0);return;}
    let stopped=false,retry,heartbeat,attempt=0,lastSeen=Date.now(),unreadTimer;
    const refreshUnread=()=>{
      clearTimeout(unreadTimer);
      unreadTimer=setTimeout(()=>api.get('/conversations').then(r=>{if(!stopped)setUnread(r.data.reduce((sum,c)=>sum+c.unread_count,0));}).catch(()=>{}),150);
    };
    const connect=()=>{
      if(stopped)return;
      setStatus(attempt?'reconnecting':'connecting');
      const ws=new WebSocket(websocketUrl());socket.current=ws;
      ws.onopen=()=>{lastSeen=Date.now();ws.send(JSON.stringify({type:'auth',token:localStorage.getItem('skillswap_token')}));};
      ws.onmessage=event=>{
        lastSeen=Date.now();let data;try{data=JSON.parse(event.data);}catch{return;}
        if(data.type==='ready'){
          attempt=0;setStatus('connected');refreshUnread();clearInterval(heartbeat);
          heartbeat=setInterval(()=>{if(Date.now()-lastSeen>45000)ws.close();else if(ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:'ping'}));},15000);
        }
        if(['message.created','messages.read','conversations.changed'].includes(data.type))refreshUnread();
        listeners.current.forEach(fn=>fn(data));
      };
      ws.onerror=()=>ws.close();
      ws.onclose=event=>{
        clearInterval(heartbeat);if(stopped)return;
        if(event.code===4401){logout();return;}
        if([4403,4429].includes(event.code)){setStatus('unavailable');return;}
        setStatus('reconnecting');retry=setTimeout(connect,Math.min(30000,1000*2**Math.min(attempt++,5))+Math.random()*500);
      };
    };
    connect();
    const online=()=>{if(socket.current?.readyState===WebSocket.CLOSED){clearTimeout(retry);connect();}};
    const visible=()=>{if(!document.hidden){refreshUnread();online();}};
    window.addEventListener('online',online);document.addEventListener('visibilitychange',visible);
    return()=>{stopped=true;clearTimeout(retry);clearTimeout(unreadTimer);clearInterval(heartbeat);socket.current?.close();socket.current=null;window.removeEventListener('online',online);document.removeEventListener('visibilitychange',visible);};
  },[user?.id,logout]);
  return <RealtimeContext.Provider value={{status,subscribe,send,unread}}>{children}</RealtimeContext.Provider>;
}
