import {createContext,useCallback,useContext,useEffect,useState} from 'react';
import api,{errorMessage} from '../services/api';
const AuthContext=createContext(null);
export const useAuth=()=>useContext(AuthContext);
export function AuthProvider({children}){
  const [user,setUser]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
  const logout=useCallback(()=>{localStorage.removeItem('skillswap_token');localStorage.removeItem('skillswap_user');setUser(null);},[]);
  const updateUser=useCallback(next=>{setUser(next);localStorage.setItem('skillswap_user',JSON.stringify(next));},[]);
  const acceptToken=useCallback(data=>{localStorage.setItem('skillswap_token',data.access_token);updateUser(data.user);return data;},[updateUser]);
  const restore=useCallback(async()=>{
    setLoading(true);setError('');
    if(!localStorage.getItem('skillswap_token')){setUser(null);setLoading(false);return;}
    try{updateUser((await api.get('/users/me')).data);}
    catch(e){if(e.response?.status===401)logout();else setError(errorMessage(e,'We could not reconnect to SkillSwap. Check your connection and try again.'));}
    finally{setLoading(false);}
  },[logout,updateUser]);
  useEffect(()=>{
    restore();
    const changed=e=>{if(e.key==='skillswap_token')restore();};
    window.addEventListener('skillswap:unauthorized',logout);window.addEventListener('storage',changed);
    return()=>{window.removeEventListener('skillswap:unauthorized',logout);window.removeEventListener('storage',changed);};
  },[restore,logout]);
  const login=async data=>acceptToken((await api.post('/auth/login',data)).data);
  const register=async data=>acceptToken((await api.post('/auth/register',data)).data);
  if(loading)return <div className="app-loading" role="status"><span className="loading-orbit"/><strong>Opening your learning space…</strong></div>;
  if(error)return <div className="app-loading"><p role="alert">{error}</p><button className="button" onClick={restore}>Reconnect</button><button className="ghost" onClick={()=>{logout();setError('');}}>Return to sign in</button></div>;
  return <AuthContext.Provider value={{user,loading,login,register,logout,acceptToken,updateUser}}>{children}</AuthContext.Provider>;
}
