(() => {
  const $ = (id) => document.getElementById(id);
  const money = (v) => v == null ? '—' : new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(v);
  const pct = (v) => v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;

  function draw(series) {
    const canvas = $('chart');
    const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.floor(rect.width * dpr); canvas.height = Math.floor(rect.height * dpr);
    const c = canvas.getContext('2d'); c.scale(dpr,dpr);
    const W=rect.width,H=rect.height,p={l:58,r:18,t:18,b:34};
    const valid=series.filter(x=>x.wma!==null && x.price>0 && x.wma>0);
    if(valid.length<2) return;
    const logs=valid.flatMap(x=>[Math.log10(x.price),Math.log10(x.wma)]);
    let ymin=Math.min(...logs), ymax=Math.max(...logs); const pad=(ymax-ymin)*.06; ymin-=pad;ymax+=pad;
    const x=(i)=>p.l+i*(W-p.l-p.r)/(valid.length-1);
    const y=(v)=>p.t+(ymax-Math.log10(v))*(H-p.t-p.b)/(ymax-ymin);

    c.clearRect(0,0,W,H); c.font='11px system-ui'; c.textBaseline='middle';
    c.strokeStyle='#26303a'; c.fillStyle='#77828f'; c.lineWidth=1;
    const lo=Math.floor(ymin), hi=Math.ceil(ymax);
    for(let n=lo;n<=hi;n++) for(const m of [1,2,5]){
      const val=m*Math.pow(10,n); const yy=y(val); if(yy<p.t||yy>H-p.b) continue;
      c.beginPath();c.moveTo(p.l,yy);c.lineTo(W-p.r,yy);c.stroke();c.fillText(`$${val>=1000?(val/1000).toFixed(val>=10000?0:1)+'k':val}`,4,yy);
    }
    for(let i=0;i<valid.length-1;i++) if(valid[i].below){
      c.fillStyle='rgba(150,72,72,.10)'; c.fillRect(x(i),p.t,Math.max(1,x(i+1)-x(i)),H-p.t-p.b);
    }
    function line(key,color,width){c.beginPath();valid.forEach((r,i)=>{const xx=x(i),yy=y(r[key]);i?c.lineTo(xx,yy):c.moveTo(xx,yy)});c.strokeStyle=color;c.lineWidth=width;c.stroke()}
    line('wma','#7e8b99',2); line('price','#edf3f8',1.6);

    c.fillStyle='#77828f'; c.textBaseline='top';
    const ticks=5; for(let t=0;t<=ticks;t++){const i=Math.round(t*(valid.length-1)/ticks); const d=new Date(valid[i].date+'T00:00:00Z'); const label=d.getUTCFullYear(); c.fillText(String(label),Math.min(W-40,Math.max(p.l,x(i)-12)),H-p.b+9)}
  }

  let current=[];
  async function load(){
    try{
      const r=await fetch('/api/series',{headers:{'Accept':'application/json'}}); const d=await r.json(); if(!r.ok) throw new Error(d.detail||d.error||'request failed');
      current=d.series; $('price').textContent=money(d.metrics.price); $('wma').textContent=money(d.metrics.wma); $('distance').textContent=pct(d.metrics.distance_pct); $('source').textContent=`source: ${d.source}`; $('updated').textContent=`updated: ${new Date(d.generated_at).toLocaleString()}`; $('status').textContent='online'; draw(current);
    }catch(e){$('status').textContent='data unavailable'; $('updated').textContent=e.message;}
  }
  let timer; addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(()=>draw(current),120)}); load();
})();
