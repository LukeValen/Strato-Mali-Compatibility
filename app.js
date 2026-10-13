/* SPDX-License-Identifier: MIT */
const BASE = './data/';
const REPORT_URL = 'https://github.com/LukeValen/Strato-Mali-Compatibility/issues/new?template=compatibility-report.yml';
const STATUS = {playable:'Jogável',ingame:'Dentro do jogo',boots:'Inicia',nothing:'Não inicia',unplayable:'Injogável'};
const els = {
  grid:document.getElementById('game-grid'),empty:document.getElementById('empty-state'),error:document.getElementById('data-error'),
  search:document.getElementById('search'),gpu:document.getElementById('gpu-filter'),status:document.getElementById('status-filter'),
  summary:document.getElementById('results-summary'),games:document.getElementById('games-count'),reports:document.getElementById('reports-count'),
  gpus:document.getElementById('gpus-count'),updated:document.getElementById('updated-at')
};
let games=[],reviews=[];
const normalize = value => String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const element = (tag,className,text) => {const node=document.createElement(tag);if(className)node.className=className;if(text!=null)node.textContent=text;return node;};

function validReview(r){return r && /^[0-9A-F]{16}$/.test(r.titleId) && Number.isInteger(r.stars) && r.stars>=0 && r.stars<=5 &&
  Object.hasOwn(STATUS,r.status) && typeof r.gpu==='string' && r.gpu.length<=100 &&
  /^https:\/\/github\.com\/LukeValen\/Strato-Mali-Compatibility\/issues\/\d+$/.test(r.url||'');}
function statusFor(list){
  // Each report remains visible. The newest report is the summary label, not a claim about every device.
  return [...list].sort((a,b)=>String(b.date).localeCompare(String(a.date)))[0]?.status;
}
function ratingFor(list){return list.reduce((sum,r)=>sum+r.stars,0)/list.length;}
function detailRow(review){
  const row=element('article','report');
  const header=element('div','report-heading');
  header.append(element('strong','',`${review.stars}/5 ★ · ${STATUS[review.status]}`),element('span','',`${review.gpu} · ${review.date||'Data não informada'}`));
  row.append(header);
  const meta=[review.emulatorVersion,review.driver].filter(Boolean).join(' · ');
  if(meta)row.append(element('p','report-meta',meta));
  if(review.notes)row.append(element('p','report-notes',review.notes));
  const source=element('a','','Ver relato no GitHub ↗');source.href=review.url;source.target='_blank';source.rel='noopener noreferrer';row.append(source);
  return row;
}
function makeCard(game,list){
  const card=element('article','game-card');
  const top=element('div','card-top'),tile=element('div','game-tile',game.title.trim().slice(0,1).toUpperCase());
  tile.setAttribute('aria-hidden','true');
  const titleWrap=element('div');titleWrap.append(element('h3','game-title',game.title),element('span','game-id',game.titleId));top.append(tile,titleWrap);card.append(top);
  const status=statusFor(list),badge=element('span',`status ${status?'status-'+status:''}`,status?STATUS[status]:'Aguardando teste');
  card.append(badge);
  const rating=element('div','rating-line');
  if(list.length){
    const average=ratingFor(list),full=Math.round(average);
    const stars=element('span','rating-stars','★'.repeat(full)+'☆'.repeat(5-full));stars.setAttribute('aria-label',`${average.toFixed(1)} de 5 estrelas`);
    rating.append(stars,element('span','rating-value',average.toFixed(1).replace('.',',')),element('span','rating-count',`(${list.length} ${list.length===1?'avaliação':'avaliações'})`));
  }else rating.append(element('span','rating-empty','Ainda sem avaliações'));
  card.append(rating);
  const bottom=element('div','card-bottom');bottom.append(element('span','',list.length?`${new Set(list.map(r=>r.gpu)).size} GPU(s) avaliada(s)`:'Seja a primeira pessoa a testar'));
  if(list.length){
    const details=element('details','reports-detail'),summary=element('summary','','Ver relatos');
    details.append(summary,...[...list].sort((a,b)=>String(b.date).localeCompare(String(a.date))).map(detailRow));
    card.append(bottom,details);
  }else{
    const link=element('a','','Avaliar ↗');link.href=REPORT_URL;link.target='_blank';link.rel='noopener noreferrer';bottom.append(link);card.append(bottom);
  }
  return card;
}
function render(){
  const query=normalize(els.search.value.trim()),gpu=els.gpu.value,status=els.status.value;
  const matches=games.map(game=>({game,list:reviews.filter(r=>r.titleId===game.titleId && (!gpu || r.gpu===gpu))}))
    .filter(({game,list})=>(!query||normalize(game.title).includes(query)||game.titleId.toLowerCase().includes(query)) &&
      (!gpu || list.length>0) && (!status || list.some(r=>r.status===status)));
  els.grid.replaceChildren(...matches.map(({game,list})=>makeCard(game,list)));
  els.empty.hidden=matches.length>0;
  els.summary.textContent=`${matches.length} ${matches.length===1?'jogo encontrado':'jogos encontrados'}${gpu?' · '+gpu:''}`;
}
async function init(){
  try{
    const [catalogResponse,reviewsResponse]=await Promise.all([fetch(BASE+'games.json'),fetch(BASE+'reviews.json',{cache:'no-cache'})]);
    if(!catalogResponse.ok||!reviewsResponse.ok)throw new Error('Data unavailable');
    const catalog=await catalogResponse.json(),data=await reviewsResponse.json();
    if(!Array.isArray(catalog)||!Array.isArray(data.reviews))throw new Error('Invalid data');
    const entries=new Map();
    for(const g of catalog)if(/^[0-9A-F]{16}$/.test(g.titleId)&&typeof g.title==='string')entries.set(g.titleId,g);
    reviews=data.reviews.filter(validReview);
    for(const r of reviews)if(!entries.has(r.titleId))entries.set(r.titleId,{titleId:r.titleId,title:r.title});
    games=[...entries.values()].sort((a,b)=>a.title.localeCompare(b.title,'pt-BR'));
    const gpus=[...new Set(reviews.map(r=>r.gpu))].sort((a,b)=>a.localeCompare(b));
    for(const gpu of gpus){const option=element('option','',gpu);option.value=gpu;els.gpu.append(option);}
    els.games.textContent=String(games.length);els.reports.textContent=String(reviews.length);els.gpus.textContent=String(gpus.length);
    if(data.generatedAt){const date=new Date(data.generatedAt);if(!Number.isNaN(date.valueOf()))els.updated.textContent=`Atualizado em ${date.toLocaleDateString('pt-BR',{timeZone:'UTC'})}`;}
    [els.search,els.gpu,els.status].forEach(input=>input.addEventListener(input===els.search?'input':'change',render));
    render();
  }catch(error){els.summary.textContent='';els.error.hidden=false;els.games.textContent=els.reports.textContent=els.gpus.textContent='—';}
}
init();
