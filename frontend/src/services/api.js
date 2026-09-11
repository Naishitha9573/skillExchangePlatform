import axios from 'axios';
const api=axios.create({baseURL:import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1'});
api.interceptors.request.use(config=>{const token=localStorage.getItem('skillswap_token'); if(token) config.headers.Authorization=`Bearer ${token}`; return config;});
api.interceptors.response.use(r=>r,e=>{if(e.response?.status===401){localStorage.removeItem('skillswap_token'); localStorage.removeItem('skillswap_user');} return Promise.reject(e);});
export default api;
