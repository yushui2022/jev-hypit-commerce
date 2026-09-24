const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
let token='', products=[], creators=[], jobs=[], currentJob=null, selected=null, polling=null, jobFilter='all';
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
const VIEWS=['match','catalog','jobs','films'];

let noticeTimer;
const notify=(text,type='info')=>{const n=$('#notice');n.textContent=text;n.className='notice-'+type;n.hidden=false;clearTimeout(noticeTimer);noticeTimer=setTimeout(()=>n.hidden=true,9000)};

async function api(path,options={}){const response=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{}),...options.headers}});if(response.status===401){$('#auth').hidden=false;throw Error('请先连接工作空间');}const body=await response.json();if(!response.ok)throw Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail));return body;}
function safeMedia(path){if(typeof path!=='string'||path.includes('..')||!['examples/assets/','productions/hd-fast/assets/','productions/advanced/assets/'].some(p=>path.startsWith(p)))return '';return '/media/'+path.split('/').map(encodeURIComponent).join('/');}
function portrait(item){const n=el('div','portrait'),url=safeMedia(item.image);if(!url)return n;if(item.sheet_cell!==null&&item.sheet_cell!==undefined){n.style.backgroundImage=`url("${url}")`;n.style.backgroundSize='400% 500%';n.style.backgroundPosition=`${item.sheet_cell%4/3*100}% ${Math.floor(item.sheet_cell/4)/4*100}%`;}else{const img=el('img');img.src=url;img.alt=item.name;img.loading='lazy';n.append(img);}return n;}
function image(item,cls){const n=el('img',cls);n.src=safeMedia(item.image);n.alt=item.name;n.loading='lazy';return n;}

function setStep(n){$$('#flow-steps span').forEach((x,i)=>x.classList.toggle('current',i===n-1))}

function view(name){
  for(const x of $$('main>section[id^="view-"]'))x.hidden=x.id!=='view-'+name;
  for(const b of $$('nav button'))b.classList.toggle('active',b.dataset.view===name);
  if(name==='jobs'||name==='films')loadJobs();
  if(name==='catalog')catalog();
  if(location.hash!=='#'+name)history.replaceState(null,'','#'+name);
}
for(const button of $$('nav button'))button.onclick=()=>view(button.dataset.view);
addEventListener('hashchange',()=>{const n=location.hash.slice(1);if(VIEWS.includes(n))view(n)});

function showProduct(){const p=products.find(x=>x.id===$('#product-select').value);if(!p)return;clearTimeout(polling);$('#run-match').disabled=false;currentJob=null;selected=null;$('#decision').hidden=true;$('#review-actions').hidden=true;$('#candidate-grid').replaceChildren();$('#empty-state').hidden=false;$('#result-status').textContent='等待输入';$('#result-status').classList.remove('loading');setStep(1);renderProduct(p);}
function renderProduct(p){$('#product-preview').replaceChildren(image(p));$('#product-name').textContent=p.name;$('#product-description').textContent=p.description;}

function catalog(){
  const q=$('#search').value.toLowerCase();
  const rows=($('#catalog-kind').value==='product'?products:creators).filter(x=>(x.name+' '+x.tags.join(' ')+' '+x.market+' '+x.language+' '+(x.category||'')).toLowerCase().includes(q));
  $('#catalog-grid').replaceChildren(...rows.map(item=>{
    const card=el('article','catalog-card');
    card.append(item.kind==='creator'?portrait(item):image(item,'product-image'));
    const copy=el('div','catalog-copy');
    copy.append(el('h3','',item.name));
    const tags=el('div');for(const t of item.tags.slice(0,4))tags.append(el('span','tag',t));
    copy.append(tags,el('p','',item.market+' / '+item.language+' · '+item.id));
    card.append(copy);
    return card;
  }));
}

async function init(){
  document.body.classList.add('booting');
  try{
    const [health,items]=await Promise.all([api('/health'),api('/catalog')]);
    products=items.items.filter(x=>x.kind==='product'&&x.active);
    creators=items.items.filter(x=>x.kind==='creator'&&x.active);
    $('#auth').hidden=true;
    $('#connection').textContent='服务已连接 · '+health.retrieval;
    $('#creator-count').textContent=creators.length;
    $('#product-count').textContent=products.length+' 件商品';
    $('#product-select').replaceChildren(...products.map(p=>{const n=el('option','',p.name);n.value=p.id;return n}));
    $('#engine option[value="jev"]').disabled=!health.jev_configured;
    $('#engine-note').textContent=health.jev_configured?'Jev 已配置。调用由服务端完成。':'本地基线无需密钥。设置 JEV_API_KEY 后可使用 Jev。';
    $('#sample-faces').replaceChildren(...creators.filter((_,i)=>i%Math.max(1,Math.floor(creators.length/5))===0).slice(0,5).map(portrait));
    showProduct();
    if(!products.length)notify('还没有商品。可通过商品库导入 JSON，或运行 creator-network seed。','error');
    const start=location.hash.slice(1);
    if(VIEWS.includes(start)&&start!=='match')view(start);
  }catch(e){notify(e.message,'error');}
  finally{document.body.classList.remove('booting');}
}

$('#connect').onclick=()=>{token=$('#token').value;$('#token').value='';init()};
$('#product-select').onchange=showProduct;
$('#catalog-kind').onchange=catalog;
$('#search').oninput=catalog;

$('#run-match').onclick=async()=>{
  try{
    $('#run-match').disabled=true;
    $('#result-status').textContent='任务已提交';
    $('#result-status').classList.add('loading');
    setStep(2);
    const job=await api('/matches',{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({product_id:$('#product-select').value,top_k:Number($('#top-k').value),engine:$('#engine').value})});
    await waitForMatch(job.id);
  }catch(e){notify(e.message,'error');$('#result-status').classList.remove('loading');$('#run-match').disabled=false;}
};

async function waitForMatch(id){
  clearTimeout(polling);
  try{
    const job=await api('/jobs/'+id);
    $('#result-status').textContent=job.status==='queued'?'排队中':job.status==='running'?'召回与决策中':job.status;
    if(['queued','running'].includes(job.status)){polling=setTimeout(()=>waitForMatch(id),800);return;}
    $('#result-status').classList.remove('loading');
    $('#run-match').disabled=false;
    if(job.status==='failed')throw Error(job.error);
    displayMatch(job);
  }catch(e){$('#result-status').classList.remove('loading');$('#run-match').disabled=false;notify(e.message,'error');}
}

function displayMatch(job){
  currentJob=job;const r=job.result;
  $('#product-select').value=r.product.id;
  renderProduct(r.product);
  selected=r.review.creator_id||r.decision.creator_id;
  $('#empty-state').hidden=true;
  $('#decision').hidden=false;
  $('#review-actions').hidden=!r.candidates.length;
  $('#result-status').textContent=r.review.status==='approved'?'已审核':r.review.status==='rejected'?'已拒绝':'等待人工审核';
  setStep(3);
  const box=el('div','decision-banner');
  box.append(el('h3','',r.review.status==='approved'?'人工审核已通过':r.review.status==='rejected'?'此匹配未采用':r.decision.provider==='jev'?'Jev 已完成候选选择':'本地检索基线 · 待人工判断'));
  box.append(el('p','',r.decision.provider==='jev'?`候选选择置信度：${(r.decision.confidence*100).toFixed(1)}%。这不是销量预测。`:'依据名称、描述和标签检索；检索分数不代表模型置信度。'));
  const trace=el('div','trace',`${r.trace.retrieval}  /  ${r.trace.eligible_count} eligible → ${r.trace.candidate_count} candidates  /  ${r.trace.total_ms} ms`);
  $('#decision').replaceChildren(box,trace);
  drawCandidates();
  $('#render').hidden=r.review.status!=='approved';
  $('#review-note').value=r.review.note||'';
}

function drawCandidates(){
  const r=currentJob.result;
  $('#candidate-grid').replaceChildren(...r.candidates.map((row,i)=>{
    const c=row.creator,n=el('button','candidate'+(c.id===selected?' selected':''));
    n.append(portrait(c),el('span','rank',String(i+1).padStart(2,'0')));
    const copy=el('div','candidate-info');
    copy.append(el('strong','',c.name));
    if(c.tags&&c.tags.length){
      const tags=el('div','candidate-tags');
      for(const t of c.tags.slice(0,3))tags.append(el('span','tag',t));
      copy.append(tags);
    }
    copy.append(el('p','',`${c.market} / ${c.language} · 检索 ${row.score.toFixed(3)} · ${row.sources.join(' + ')}`));
    n.append(copy);
    n.onclick=()=>{selected=c.id;drawCandidates();$('#render').hidden=true;};
    return n;
  }));
}

async function review(action){
  try{
    const job=await api('/matches/'+currentJob.id+'/review',{method:'POST',body:JSON.stringify({action,creator_id:selected,note:$('#review-note').value})});
    displayMatch(job);
    notify(action==='approve'?'审核已记录，可以生成两个水印版本。':'已记录不采用此匹配。',action==='approve'?'success':'info');
  }catch(e){notify(e.message,'error');}
}
$('#approve').onclick=()=>review('approve');
$('#reject').onclick=()=>review('reject');
$('#render').onclick=async()=>{
  try{
    await api('/renders',{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({match_job_id:currentJob.id})});
    notify('视频任务已加入队列。请在任务页查看进度，完成后会提供两个版本。','success');
    view('jobs');
  }catch(e){notify(e.message,'error');}
};

const STATUS_LABEL={completed:'已完成',failed:'失败',queued:'排队中',running:'进行中'};
const KIND_LABEL={match:'匹配',render:'视频'};
const isActive=j=>['queued','running'].includes(j.status);

function renderJobSummary(){
  const stats=[['全部任务',jobs.length],['已完成',jobs.filter(j=>j.status==='completed').length],['失败',jobs.filter(j=>j.status==='failed').length],['进行中',jobs.filter(isActive).length]];
  $('#jobs-summary').replaceChildren(...stats.map(([label,n])=>{
    const c=el('div','job-stat');
    c.append(el('strong','',String(n)),el('span','',label));
    return c;
  }));
}

function renderJobFilters(){
  const defs=[['all','全部'],['active','进行中'],['completed','已完成'],['failed','失败']];
  const count=k=>k==='all'?jobs.length:k==='active'?jobs.filter(isActive).length:jobs.filter(j=>j.status===k).length;
  $('#jobs-filters').replaceChildren(...defs.map(([k,label])=>{
    const b=el('button','filter-chip'+(jobFilter===k?' active':''),label+' '+count(k));
    b.onclick=()=>{jobFilter=k;renderJobFilters();renderJobRows();};
    return b;
  }));
}

function renderJobRows(){
  const visible=jobs.filter(j=>jobFilter==='all'||(jobFilter==='active'?isActive(j):j.status===jobFilter));
  $('#jobs-list').replaceChildren(...visible.map(j=>{
    const item=el('div','job-item');
    const n=el('div','job-row'+(j.status==='failed'?' is-failed':''));
    n.append(el('span','badge '+j.status,STATUS_LABEL[j.status]||j.status));
    n.append(el('span','kind-chip',KIND_LABEL[j.kind]||j.kind));
    const main=el('div','job-main');
    main.append(el('strong','',j.kind==='match'?'达人匹配 · '+j.payload.product_id:'双水印视频'));
    if(j.status==='failed'&&j.error)main.append(el('div','job-error',j.error));
    n.append(main);
    const meta=el('div','job-meta');
    meta.append(el('time','',new Date(j.created*1000).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})),el('code','',j.id.slice(0,12)));
    n.append(meta);
    const actions=el('div','job-actions');
    if(j.kind==='match'&&j.status==='completed'){const b=el('button','','查看审核');b.onclick=()=>{displayMatch(j);view('match')};actions.append(b);}
    if(j.status==='failed'){const b=el('button','','重试');b.onclick=async()=>{try{await api('/jobs/'+j.id+'/retry',{method:'POST'});loadJobs();}catch(e){notify(e.message,'error')}};actions.append(b);}
    const detail=el('div','job-detail');detail.hidden=true;
    const log=el('button','','详情');
    log.onclick=async()=>{
      if(detail.hidden){
        detail.hidden=false;log.textContent='收起';
        if(!detail.childElementCount){
          detail.textContent='加载中…';
          try{detail.textContent=JSON.stringify(await api('/jobs/'+j.id+'/events'),null,2);}catch(e){detail.textContent=e.message;}
        }
      }else{detail.hidden=true;log.textContent='详情';}
    };
    actions.append(log);
    n.append(actions);
    item.append(n,detail);
    return item;
  }));
  if(!visible.length){
    const e=el('div','empty-jobs');
    e.append(el('strong','',jobs.length?'当前筛选下没有任务':'尚无任务记录'),el('p','muted',jobs.length?'切换上方筛选查看其他状态的任务。':'在匹配工作台选择商品并提交匹配，任务记录会显示在这里。'));
    $('#jobs-list').append(e);
  }
}

async function loadJobs(){
  try{
    jobs=(await api('/jobs')).jobs;
    renderJobSummary();
    renderJobFilters();
    renderJobRows();
    $('#rendered-films').replaceChildren(...jobs.filter(j=>j.kind==='render'&&j.status==='completed').map(j=>{
      const n=el('article');
      n.append(el('h3','','审核交付 · '+j.id.slice(0,8)));
      const grid=el('div','delivered-videos');
      for(const file of j.result.files){
        const item=el('div','delivered-item');
        const v=el('video');
        v.controls=true;v.preload='metadata';v.src=file.url;
        const b=el('button','',file.brand==='guanyi'?'下载贯一科技版':'下载 Yeadon 版');
        b.onclick=()=>download(file.url,file.brand+'.mp4');
        item.append(v,b);
        grid.append(item);
      }
      n.append(grid);
      return n;
    }));
  }catch(e){notify(e.message,'error');}
}

async function download(url,name){
  try{
    const r=await fetch(url,{headers:token?{Authorization:'Bearer '+token}:{}});
    if(!r.ok)throw Error('下载失败');
    const u=URL.createObjectURL(await r.blob());
    const a=el('a');a.href=u;a.download=name;a.click();
    setTimeout(()=>URL.revokeObjectURL(u),30000);
  }catch(e){notify(e.message,'error')}
}

$('#refresh-jobs').onclick=loadJobs;
$('#import-button').onclick=()=>$('#import-file').click();
$('#import-file').onchange=async e=>{
  try{
    const body=JSON.parse(await e.target.files[0].text());
    await api('/catalog',{method:'POST',body:JSON.stringify(body)});
    await init();catalog();
    notify('商品库已更新。','success');
  }catch(e){notify(e.message,'error');}
  finally{e.target.value='';}
};

init();
