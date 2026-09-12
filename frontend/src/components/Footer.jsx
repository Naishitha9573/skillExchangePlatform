import {Link} from 'react-router-dom';
import {ArrowRightLeft} from 'lucide-react';
import BrandMark from './BrandMark';
const groups=[
  ['Product',[['Explore skills','/feed'],['Smart matching','/innovation'],['Messages','/messages'],['Sessions','/sessions']]],
  ['Platform',[['How it works','/#how-it-works'],['Community','/feed?view=people'],['Get started','/register']]],
  ['Company',[['About SkillSwap','/#why-skillswap'],['Contact','mailto:hello@skillswap.ai']]],
  ['Legal',[['Privacy','/privacy'],['Terms','/terms']]],
  ['Account',[['Log in','/login'],['Register','/register']]],
];
export default function Footer() {
  return <footer className="site-footer"><div className="footer-inner"><div className="footer-brand"><Link to="/" className="brand"><span className="brandIcon"><BrandMark size={38}/></span>SkillSwap</Link><p>Learn from people.<br/>Share what you know.<br/>Grow together.</p></div><div className="footer-links">{groups.map(([title,links])=><div key={title}><strong>{title}</strong>{links.map(([label,to])=>to.startsWith('mailto:')?<a key={label} href={to}>{label}</a>:<Link to={to} key={label}>{label}</Link>)}</div>)}</div></div><div className="footer-bottom"><span>© 2026 SkillSwap. All rights reserved.</span><span className="footer-mini"><ArrowRightLeft size={13}/> A little knowledge goes both ways.</span></div></footer>;
}
