import {useEffect,useRef} from 'react';
import {X} from 'lucide-react';
export default function Modal({title,children,onClose,busy=false}){
  const ref=useRef(null);
  useEffect(()=>{const dialog=ref.current;dialog.showModal();return()=>dialog.close();},[]);
  return <dialog ref={ref} className="confirmation-dialog" aria-labelledby="dialog-title" onCancel={e=>{e.preventDefault();if(!busy)onClose();}} onClick={e=>{if(e.target===ref.current&&!busy)onClose();}}><div className="dialog-content"><div className="dialog-header"><h2 id="dialog-title">{title}</h2><button className="ghost icon-button" aria-label="Close dialog" disabled={busy} onClick={onClose}><X size={19}/></button></div>{children}</div></dialog>;
}
