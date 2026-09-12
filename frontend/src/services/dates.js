export function asDate(value){return value instanceof Date?value:new Date(value&&!/(Z|[+-]\d\d:\d\d)$/.test(value)?value+'Z':value);}
export const dateTime=value=>asDate(value).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
export const timeOnly=value=>asDate(value).toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});
export function localInput(value=new Date()){
  const date=asDate(value);
  return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);
}
export const timeZone=Intl.DateTimeFormat().resolvedOptions().timeZone;
