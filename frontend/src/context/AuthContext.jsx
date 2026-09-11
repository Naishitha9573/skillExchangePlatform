import {createContext,useContext,useEffect,useState} from 'react'; import api from '../services/api';
const C=createContext(null); export const useAuth=()=>useContext(C);
export function AuthProvider({children}){const [user,setUser]=useState(()=>JSON.parse(localStorage.getItem('skillswap_user')||'null')); const [loading,setLoading]=useState(true);
useEffect(()=>{const t=localStorage.getItem('skillswap_token'); if(!t){setLoading(false);return;} api.get('/users/me').then(r=>{setUser(r.data);localStorage.setItem('skillswap_user',JSON.stringify(r.data));}).catch(()=>{localStorage.clear();setUser(null)}).finally(()=>setLoading(false));},[]);
const login=async(data)=>{const r=await api.post('/auth/login',data); localStorage.setItem('skillswap_token',r.data.access_token);localStorage.setItem('skillswap_user',JSON.stringify(r.data.user));setUser(r.data.user);return r.data};
const register=async(data)=>{const r=await api.post('/auth/register',data);localStorage.setItem('skillswap_token',r.data.access_token);localStorage.setItem('skillswap_user',JSON.stringify(r.data.user));setUser(r.data.user);return r.data};
const logout=()=>{localStorage.removeItem('skillswap_token');localStorage.removeItem('skillswap_user');setUser(null)}; return <C.Provider value={{user,loading,login,register,logout}}>{!loading&&children}</C.Provider>}
