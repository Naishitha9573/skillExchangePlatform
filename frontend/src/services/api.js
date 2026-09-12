import axios from 'axios';
const api=axios.create({baseURL:import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1',timeout:20000});
api.interceptors.request.use(config=>{const token=localStorage.getItem('skillswap_token'); if(token) config.headers.Authorization=`Bearer ${token}`; return config;});
api.interceptors.response.use(r=>r,e=>{if(e.response?.status===401&&!e.config?.url?.startsWith('/auth/')){localStorage.removeItem('skillswap_token');localStorage.removeItem('skillswap_user');window.dispatchEvent(new Event('skillswap:unauthorized'));}return Promise.reject(e);});
export function errorMessage(error,fallback='Something went wrong. Please try again.'){
  const detail=error?.response?.data?.detail;
  if(typeof detail==='string')return detail;
  if(Array.isArray(detail))return detail.map(item=>item.msg?.replace(/^Value error, /,'')).filter(Boolean).join('. ');
  return fallback;
}
export function websocketUrl(){
  const url=new URL(api.defaults.baseURL,window.location.origin);
  url.protocol=url.protocol==='https:'?'wss:':'ws:';
  url.pathname=url.pathname.replace(/\/$/,'')+'/ws';url.search='';
  return url.toString();
}
export default api;
