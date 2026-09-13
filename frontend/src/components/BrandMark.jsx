export default function BrandMark({size=24, className=''}) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <path d="M30 12H16a8 8 0 0 0 0 16h3" stroke="#2563EB" strokeWidth="5" strokeLinecap="round"/>
      <path d="m25 6 6 6-6 6" stroke="#2563EB" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M10 28h14a8 8 0 0 0 0-16h-3" stroke="#06B6D4" strokeWidth="5" strokeLinecap="round"/>
      <path d="m15 22-6 6 6 6" stroke="#F97340" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
