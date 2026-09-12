import {useEffect,useRef,useState} from 'react';
import {Link,useLocation,useNavigate} from 'react-router-dom';
import {ArrowRight,Check,Eye,EyeOff,Sparkles} from 'lucide-react';
import {useAuth} from '../context/AuthContext';
import api,{errorMessage} from '../services/api';

const safeReturn=path=>path?.startsWith('/')&&!path.startsWith('//')&&!path.startsWith('/auth/')?path:'/dashboard';
function GoogleButton({returnTo='/dashboard'}){
  const [enabled,setEnabled]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>{api.get('/auth/providers').then(r=>setEnabled(r.data.google)).catch(()=>setEnabled(false));},[]);
  const start=async()=>{
    setBusy(true);setError('');
    try{const {data}=await api.get('/auth/google/authorize',{withCredentials:true});const url=new URL(data.authorization_url);sessionStorage.setItem('skillswap_google_state',url.searchParams.get('state'));sessionStorage.setItem('skillswap_return_to',safeReturn(returnTo));window.location.assign(url.toString());}
    catch(e){setError(errorMessage(e,'Google sign-in is unavailable. Please use email.'));setBusy(false);}
  };
  return <><button type="button" className="button secondary full google-button" disabled={!enabled||busy} onClick={start}><span className="google-mark" aria-hidden="true">G</span>{busy?'Opening Google…':'Continue with Google'}</button>{enabled===false&&<p className="auth-helper">Google sign-in is currently unavailable. Continue with email below.</p>}{error&&<div className="error" role="alert">{error}</div>}<div className="auth-divider"><span>or with email</span></div></>;
}
export function Login(){
  const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[error,setError]=useState(''),[loading,setLoading]=useState(false);
  const {login}=useAuth(),navigate=useNavigate(),location=useLocation();
  const returnTo=safeReturn(location.state?.from?.pathname+(location.state?.from?.search||''));
  const submit=async e=>{e.preventDefault();setLoading(true);setError('');try{await login({email,password});navigate(returnTo,{replace:true});}catch(x){setError(errorMessage(x,'Unable to sign in. Check your connection and try again.'));}finally{setLoading(false);}};
  return <AuthShell title="Welcome back." subtitle="Your next chapter is waiting."><GoogleButton returnTo={returnTo}/><form onSubmit={submit} className="form"><Field label="Email address" value={email} set={setEmail} type="email" autoComplete="email"/><Field label="Password" value={password} set={setPassword} type="password" autoComplete="current-password"/>{error&&<div className="error" role="alert">{error}</div>}<button className="button full" disabled={loading}>{loading?'Signing in…':'Sign in'}<ArrowRight size={17}/></button></form><p className="authfoot">New here? <Link to="/register">Create an account</Link></p></AuthShell>;
}
export function Register(){
  const [form,setForm]=useState({full_name:'',email:'',password:'',location:''}),[error,setError]=useState(''),[loading,setLoading]=useState(false);
  const {register}=useAuth(),navigate=useNavigate();const set=(key,value)=>setForm(current=>({...current,[key]:value}));
  const submit=async e=>{e.preventDefault();setLoading(true);setError('');try{await register(form);navigate('/dashboard',{replace:true});}catch(x){setError(errorMessage(x,'Unable to create your account. Please try again.'));}finally{setLoading(false);}};
  return <AuthShell title="Something to teach. So much to learn." subtitle="Start your own circle of shared knowledge."><GoogleButton/><form onSubmit={submit} className="form"><Field label="Full name" value={form.full_name} set={v=>set('full_name',v)} minLength={2} maxLength={120} autoComplete="name"/><Field label="Email address" value={form.email} set={v=>set('email',v)} type="email" autoComplete="email"/><Field label="Location (optional)" value={form.location} set={v=>set('location',v)} required={false} maxLength={120} placeholder="City or time zone" autoComplete="address-level2"/><Field label="Password" value={form.password} set={v=>set('password',v)} type="password" autoComplete="new-password" minLength={8} maxLength={128}/><p className="auth-helper">Use 8+ characters, including uppercase, lowercase, and a number.</p>{error&&<div className="error" role="alert">{error}</div>}<button className="button full" disabled={loading}>{loading?'Creating your account…':'Create account'}<ArrowRight size={17}/></button><p className="auth-helper">By joining, you agree to our <Link to="/terms">Terms</Link> and <Link to="/privacy">Privacy Policy</Link>.</p></form><p className="authfoot">Already part of the circle? <Link to="/login">Sign in</Link></p></AuthShell>;
}
export function GoogleCallback(){
  const [error,setError]=useState(''),started=useRef(false),{acceptToken}=useAuth(),navigate=useNavigate();
  useEffect(()=>{
    if(started.current)return;started.current=true;
    const params=new URLSearchParams(window.location.search),state=params.get('state'),code=params.get('code');
    const saved=sessionStorage.getItem('skillswap_google_state');
    if(params.has('error')||!state||!code||!saved||saved!==state){setError('Google sign-in was cancelled or expired. Start again from the sign-in page.');return;}
    api.post('/auth/google/callback',{state,code},{withCredentials:true}).then(r=>{
      const returnTo=safeReturn(sessionStorage.getItem('skillswap_return_to'));
      sessionStorage.removeItem('skillswap_google_state');sessionStorage.removeItem('skillswap_return_to');
      acceptToken(r.data);navigate(returnTo,{replace:true});
    }).catch(e=>setError(errorMessage(e,'Google sign-in could not be completed. Please try again.')));
  },[acceptToken,navigate]);
  return <AuthShell title={error?'Let’s try that again.':'One moment…'} subtitle={error?'Your account is waiting for you.':'Finishing your secure Google sign-in.'}>{error?<><p className="error" role="alert">{error}</p><Link className="button full" to="/login">Return to sign in</Link></>:<div className="loading" role="status">Connecting your account…</div>}</AuthShell>;
}
function Field({label,value,set,type='text',required=true,...props}){
  const [visible,setVisible]=useState(false);
  return <label className="field"><span>{label}</span><div className="auth-input"><input required={required} value={value} onChange={e=>set(e.target.value)} type={type==='password'&&visible?'text':type} {...props}/>{type==='password'&&<button className="ghost icon-button" type="button" aria-label={visible?'Hide password':'Show password'} onClick={()=>setVisible(!visible)}>{visible?<EyeOff size={17}/>:<Eye size={17}/>}</button>}</div></label>;
}
function AuthShell({title,subtitle,children}){
  return <main className="authpage premium-auth"><aside className="auth-story"><div className="eyebrow"><Sparkles size={15}/> Grow through giving</div><h2>Your knowledge<br/>is someone else’s<br/><em>next big thing.</em></h2><p>Meet your people. Share what you know. Make space for something new.</p><div className="auth-promises">{['Thoughtful skill exchanges','Conversations that stay connected','Learning sessions, right here'].map(text=><span key={text}><Check size={16}/>{text}</span>)}</div></aside><div className="authcard"><Link to="/" className="authlogo"><Sparkles size={18}/> SkillSwap</Link><h1>{title}</h1><p>{subtitle}</p>{children}</div></main>;
}
