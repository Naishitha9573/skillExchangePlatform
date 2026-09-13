import {useState} from 'react';
import {Link,useLocation,useNavigate} from 'react-router-dom';
import {ArrowRight,Check,Eye,EyeOff} from 'lucide-react';
import {useAuth} from '../context/AuthContext';
import {errorMessage} from '../services/api';
import BrandMark from '../components/BrandMark';
import ExchangeVisual from '../components/ExchangeVisual';

const safeReturn=path=>path?.startsWith('/')&&!path.startsWith('//')&&!path.startsWith('/auth/')?path:'/dashboard';
export function Login(){
  const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[error,setError]=useState(''),[loading,setLoading]=useState(false);
  const {login}=useAuth(),navigate=useNavigate(),location=useLocation();
  const returnTo=safeReturn(location.state?.from?.pathname+(location.state?.from?.search||''));
  const submit=async e=>{e.preventDefault();setLoading(true);setError('');try{await login({email,password});navigate(returnTo,{replace:true});}catch(x){setError(errorMessage(x,'Unable to sign in. Check your connection and try again.'));}finally{setLoading(false);}};
  return <AuthShell title="Welcome back." subtitle="Your next learning moment is waiting."><form onSubmit={submit} className="form"><Field label="Email address" value={email} set={setEmail} type="email" autoComplete="email"/><Field label="Password" value={password} set={setPassword} type="password" autoComplete="current-password"/>{error&&<div className="error" role="alert">{error}</div>}<button className="button full" disabled={loading}>{loading?'Signing in…':'Sign in'}<ArrowRight size={17}/></button></form><p className="authfoot">New here? <Link to="/register" state={{from:location.state?.from}}>Create an account</Link></p></AuthShell>;
}
export function Register(){
  const [form,setForm]=useState({full_name:'',email:'',password:'',location:''}),[error,setError]=useState(''),[loading,setLoading]=useState(false);
  const {register}=useAuth(),navigate=useNavigate(),location=useLocation();const set=(key,value)=>setForm(current=>({...current,[key]:value}));
  const submit=async e=>{e.preventDefault();setLoading(true);setError('');try{await register(form);navigate(safeReturn(location.state?.from?.pathname+(location.state?.from?.search||'')),{replace:true});}catch(x){setError(errorMessage(x,'Unable to create your account. Please try again.'));}finally{setLoading(false);}};
  return <AuthShell title="Start exchanging skills." subtitle="Teach something. Learn something."><form onSubmit={submit} className="form"><Field label="Full name" value={form.full_name} set={v=>set('full_name',v)} minLength={2} maxLength={120} autoComplete="name"/><Field label="Email address" value={form.email} set={v=>set('email',v)} type="email" autoComplete="email"/><Field label="Location (optional)" value={form.location} set={v=>set('location',v)} required={false} maxLength={120} placeholder="City or time zone" autoComplete="address-level2"/><Field label="Password" value={form.password} set={v=>set('password',v)} type="password" autoComplete="new-password" minLength={8} maxLength={128}/><p className="auth-helper">Use 8+ characters, including uppercase, lowercase, and a number.</p>{error&&<div className="error" role="alert">{error}</div>}<button className="button full" disabled={loading}>{loading?'Creating your account…':'Create account'}<ArrowRight size={17}/></button><p className="auth-helper">By joining, you agree to our <Link to="/terms">Terms</Link> and <Link to="/privacy">Privacy Policy</Link>.</p></form><p className="authfoot">Already part of the circle? <Link to="/login">Sign in</Link></p></AuthShell>;
}
function Field({label,value,set,type='text',required=true,...props}){
  const [visible,setVisible]=useState(false);
  return <label className="field"><span>{label}</span><div className="auth-input"><input required={required} value={value} onChange={e=>set(e.target.value)} type={type==='password'&&visible?'text':type} {...props}/>{type==='password'&&<button className="ghost icon-button" type="button" aria-label={visible?'Hide password':'Show password'} onClick={()=>setVisible(!visible)}>{visible?<EyeOff size={17}/>:<Eye size={17}/>}</button>}</div></label>;
}
function AuthShell({title,subtitle,children}){
  return <main className="authpage premium-auth"><aside className="auth-story"><div className="eyebrow"><span className="eyebrow-dot"/> A little knowledge goes a long way</div><h2>You have something<br/>worth <em>sharing.</em></h2><p>Bring a skill. Find your people. Discover what you can learn from each other.</p><ExchangeVisual compact/><div className="auth-promises">{['Teach & learn','Chat & connect','Meet & grow'].map(text=><span key={text}><Check size={16}/>{text}</span>)}</div></aside><div className="authcard"><Link to="/" className="authlogo"><BrandMark size={30}/> SkillSwap</Link><h1>{title}</h1><p>{subtitle}</p>{children}</div></main>;
}
