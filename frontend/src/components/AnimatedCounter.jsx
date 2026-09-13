import {useEffect,useRef,useState} from 'react';
export default function AnimatedCounter({to,duration=1200,decimals=0,suffix='',prefix='',className=''}) {
  const [display,setDisplay]=useState(Number(to)||0),ref=useRef(null);
  useEffect(()=>{
    const target=Number(to)||0;
    if(window.matchMedia('(prefers-reduced-motion: reduce)').matches||!('IntersectionObserver' in window)){setDisplay(target);return;}
    let frame,stopped=false;
    const observer=new IntersectionObserver(([entry])=>{
      if(!entry.isIntersecting)return;
      observer.disconnect();
      const start=performance.now();
      const step=now=>{if(stopped)return;const progress=Math.min((now-start)/duration,1);setDisplay((1-Math.pow(1-progress,3))*target);if(progress<1)frame=requestAnimationFrame(step);};
      frame=requestAnimationFrame(step);
    },{threshold:.3});
    if(ref.current)observer.observe(ref.current);
    return()=>{stopped=true;observer.disconnect();cancelAnimationFrame(frame);};
  },[to,duration]);
  return <span ref={ref} className={className}>{prefix}{decimals?display.toFixed(decimals):Math.round(display)}{suffix}</span>;
}
