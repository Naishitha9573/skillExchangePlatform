import {useEffect,useRef} from 'react';

export default function useReveal(dependency) {
  const ref=useRef(null);
  useEffect(()=>{
    const nodes=ref.current?.querySelectorAll('[data-reveal]')||[];
    if(window.matchMedia('(prefers-reduced-motion: reduce)').matches||!('IntersectionObserver' in window))return;
    const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{
      if(entry.isIntersecting){entry.target.classList.add('revealed');observer.unobserve(entry.target);}
    }),{threshold:.08});
    nodes.forEach(node=>{node.classList.add('will-reveal');observer.observe(node);});
    return()=>observer.disconnect();
  },[dependency]);
  return ref;
}
