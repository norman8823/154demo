export default function ({parentElement, data: workbook, key}) {
  const root=parentElement.querySelector('.excel-viewer');
  const desktop=window.matchMedia('(min-width:1024px)');
  const node=(tag,text,cls)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;};
  if(!desktop.matches){root.replaceChildren(node('p','Source inspection is available on desktop.'));return;}
  // Only trusted component markup is created here; workbook strings remain text.
  const letters=column=>{let s='';while(column>0){column--;s=String.fromCharCode(65+column%26)+s;column=Math.floor(column/26);}return s;};
  const names=Object.keys(workbook.sheets), states=new Map();
  let active=workbook.initial_sheet,data=workbook.sheets[active];
  const parse=value=>{const m=/^([A-Z]{1,3})([1-9]\d*)$/.exec(value.trim().toUpperCase());if(!m)return null;const c=[...m[1]].reduce((n,x)=>n*26+x.charCodeAt(0)-64,0),r=Number(m[2]);return r<=data.rows&&c<=data.columns?[r,c]:null;};
  let [row,col]=parse(data.initial),rowCount=12,colCount=6;
  let firstRow=Math.max(1,row-5),firstCol=Math.max(1,col-2);
  const coord=()=>letters(col)+row;
  const toolbar=node('div',undefined,'formula-toolbar');
  const nameBox=node('input',undefined,'name-box');nameBox.setAttribute('aria-label','Selected cell');nameBox.title='Enter a coordinate and press Enter';nameBox.spellcheck=false;
  const fx=node('span','ƒx','fx');fx.setAttribute('aria-hidden','true');
  const formula=node('output',undefined,'formula-bar');formula.setAttribute('aria-label','Original formula or raw value');formula.tabIndex=0;toolbar.append(nameBox,fx,formula);
  const status=node('p','','grid-status');status.setAttribute('role','status');
  const range=node('p',undefined,'grid-range');
  const surface=node('div',undefined,'worksheet-surface');
  const table=node('table',undefined,'source-grid');table.id='source-grid-'+key.replace(/[^a-zA-Z0-9_-]/g,'_');table.setAttribute('role','grid');table.setAttribute('aria-readonly','true');
  const bars={};
  for(const axis of ['vertical','horizontal']){
    const track=node('div',undefined,'worksheet-scrollbar '+axis),thumb=node('div',undefined,'scrollbar-thumb');
    track.setAttribute('role','scrollbar');track.setAttribute('aria-orientation',axis);track.setAttribute('aria-label',axis==='vertical'?'Worksheet rows':'Worksheet columns');track.setAttribute('aria-controls',table.id);track.tabIndex=0;track.append(thumb);bars[axis]={track,thumb};
  }
  surface.append(table,bars.vertical.track,bars.horizontal.track,node('div',undefined,'scrollbar-corner'));
  const tabrail=node('div',undefined,'worksheet-tabrail'),tabs=node('div',undefined,'worksheet-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Original worksheets');
  const previous=node('button','‹','tab-overflow'),next=node('button','›','tab-overflow');
  previous.type=next.type='button';previous.setAttribute('aria-label','Previous worksheets');next.setAttribute('aria-label','Next worksheets');
  for(const name of names){const tab=node('button',name,'worksheet-tab');tab.type='button';tab.setAttribute('role','tab');tab.setAttribute('data-sheet',name);tab.onclick=()=>switchSheet(name);tabs.append(tab);}
  tabrail.append(previous,tabs,next);
  const details=node('details',undefined,'source-details'),provenance=node('dl');
  details.append(node('summary','Cell provenance & original units'),provenance,node('p','Read-only source snapshot. Original formulas are displayed, never executed. Merged layouts and artwork are not reproduced.','source-note'));
  root.replaceChildren(toolbar,status,range,surface,tabrail,details);
  function clampView(){firstRow=Math.max(1,Math.min(firstRow,Math.max(1,data.rows-rowCount+1)));firstCol=Math.max(1,Math.min(firstCol,Math.max(1,data.columns-colCount+1)));}
  function reveal(){if(row<firstRow)firstRow=row;if(row>=firstRow+rowCount)firstRow=row-rowCount+1;if(col<firstCol)firstCol=col;if(col>=firstCol+colCount)firstCol=col-colCount+1;clampView();}
  function updateDetails(record){
    const fields=[['Source coordinate',active+' · '+coord()],['Source label',record.label||'No row label recorded'],['Original observed value',record.observed??'(blank)'],['Value provenance',record.origin||'Original workbook blank cell'],['Original number format',record.format||'General']];
    if(record.standardized!==undefined&&record.standardized!=='')fields.push(['Source-unit multiplier',record.scale||'Not recorded'],['Verified standardized value',record.standardized+' '+record.currency],['Reported period',record.period||'Not recorded']);
    if(record.comment)fields.push(['Original cell comment',record.comment]);
    provenance.replaceChildren(...fields.flatMap(([label,value])=>[node('dt',label),node('dd',value)]));
  }
  function syncBar(axis){
    const {track,thumb}=bars[axis],vertical=axis==='vertical';
    const total=vertical?data.rows:data.columns,count=vertical?rowCount:colCount,start=vertical?firstRow:firstCol;
    const length=vertical?track.clientHeight:track.clientWidth,max=Math.max(1,total-count+1);
    const size=Math.min(length,Math.max(24,length*Math.min(1,count/total))),travel=length-size;
    thumb.style[vertical?'height':'width']=size+'px';thumb.style[vertical?'top':'left']=(max===1?0:(start-1)/(max-1)*travel)+'px';
    track.setAttribute('aria-valuemin','1');track.setAttribute('aria-valuemax',max);track.setAttribute('aria-valuenow',start);track.setAttribute('aria-disabled',String(max===1));
    track.setAttribute('aria-valuetext',(vertical?'Rows ':'Columns ')+start+'–'+Math.min(total,start+count-1)+' of '+total);
  }
  function syncTabs(){
    const max=Math.max(0,tabs.scrollWidth-tabs.clientWidth);previous.disabled=tabs.scrollLeft<=1;next.disabled=tabs.scrollLeft>=max-1;
    previous.hidden=next.hidden=max<=1;
  }
  function render(focus=false){
    clampView();const selected=coord(),record=data.cells[selected]||{};
    nameBox.value=selected;formula.textContent=record.bar??'';formula.setAttribute('data-coordinate',selected);updateDetails(record);
    const lastRow=Math.min(data.rows,firstRow+rowCount-1),lastCol=Math.min(data.columns,firstCol+colCount-1);
    const visible=row>=firstRow&&row<=lastRow&&col>=firstCol&&col<=lastCol;
    range.textContent=active+' · '+letters(firstCol)+firstRow+':'+letters(lastCol)+lastRow+(visible?'':' · '+selected+' selected outside view');
    table.setAttribute('aria-label',active+' original worksheet');table.setAttribute('aria-rowcount',data.rows+1);table.setAttribute('aria-colcount',data.columns+1);table.tabIndex=visible?-1:0;
    const head=node('thead'),header=node('tr');header.setAttribute('role','row');header.append(node('th',''));
    for(let c=firstCol;c<=lastCol;c++){const th=node('th',letters(c),c===col?'selected-header':'');th.setAttribute('scope','col');th.setAttribute('role','columnheader');header.append(th);}head.append(header);
    const body=node('tbody');
    for(let r=firstRow;r<=lastRow;r++){
      const tr=node('tr');tr.setAttribute('role','row');tr.setAttribute('aria-rowindex',r+1);
      const th=node('th',String(r),r===row?'selected-header':'');th.setAttribute('scope','row');th.setAttribute('role','rowheader');tr.append(th);
      for(let c=firstCol;c<=lastCol;c++){
        const address=letters(c)+r,cell=data.cells[address]||{},td=node('td',cell.display??'',cell.bold?'source-bold':'');
        td.setAttribute('role','gridcell');td.setAttribute('data-coordinate',address);td.setAttribute('aria-colindex',c+1);td.setAttribute('aria-label',address+': '+(cell.display??'(blank)'));
        const selectedCell=address===selected;td.setAttribute('aria-selected',String(selectedCell));td.tabIndex=selectedCell?0:-1;if(selectedCell)td.classList.add('source-target');td.title=address;tr.append(td);
      }body.append(tr);
    }table.replaceChildren(head,body);
    for(const tab of tabs.children){const selectedTab=tab.dataset.sheet===active;tab.setAttribute('aria-selected',String(selectedTab));tab.tabIndex=selectedTab?0:-1;}
    syncBar('vertical');syncBar('horizontal');syncTabs();
    if(focus)table.querySelector('[aria-selected="true"]').focus({preventScroll:true});
  }
  function select(r,c,focus=true){row=r;col=c;status.textContent='';reveal();render(focus);}
  function moveView(axis,start){if(axis==='vertical')firstRow=start;else firstCol=start;render();}
  function switchSheet(name){
    if(name===active)return;
    states.set(active,{row,col,firstRow,firstCol});active=name;data=workbook.sheets[name];
    if(name===workbook.citation.sheet){[row,col]=parse(workbook.citation.cell);firstRow=Math.max(1,row-5);firstCol=Math.max(1,col-2);}
    else if(states.has(name))({row,col,firstRow,firstCol}=states.get(name));
    else{row=col=firstRow=firstCol=1;}
    status.textContent='';render();
    const tab=[...tabs.children].find(t=>t.dataset.sheet===name);
    if(tab.offsetLeft<tabs.scrollLeft)tabs.scrollLeft=tab.offsetLeft;
    else if(tab.offsetLeft+tab.offsetWidth>tabs.scrollLeft+tabs.clientWidth)tabs.scrollLeft=tab.offsetLeft+tab.offsetWidth-tabs.clientWidth;
    syncTabs();
  }
  const click=event=>{const cell=event.target.closest('[role="gridcell"]');if(cell)select(...parse(cell.dataset.coordinate));};
  const keydown=event=>{
    if(event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
    const delta={ArrowUp:[-1,0],ArrowDown:[1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]}[event.key];
    if(!delta)return;event.preventDefault();event.stopPropagation();select(Math.max(1,Math.min(data.rows,row+delta[0])),Math.max(1,Math.min(data.columns,col+delta[1])));
  };
  const jump=event=>{if(event.key!=='Enter')return;event.preventDefault();const target=parse(nameBox.value);if(target)select(...target);else{nameBox.value=coord();status.textContent='That coordinate is outside the original worksheet. Selection is unchanged.';}};
  table.addEventListener('click',click);table.addEventListener('keydown',keydown);nameBox.addEventListener('keydown',jump);nameBox.addEventListener('blur',()=>nameBox.value=coord());
  // Pointer-only virtual scrollbars: there are deliberately no wheel handlers.
  const cleanup=[];
  for(const axis of ['vertical','horizontal']){
    const {track,thumb}=bars[axis],vertical=axis==='vertical';let dragging=null;
    const metrics=()=>{const rect=track.getBoundingClientRect(),length=vertical?rect.height:rect.width,size=vertical?thumb.offsetHeight:thumb.offsetWidth;return{origin:vertical?rect.top:rect.left,travel:Math.max(1,length-size),size,max:Math.max(1,(vertical?data.rows-rowCount:data.columns-colCount)+1)};};
    const point=event=>vertical?event.clientY:event.clientX;
    const move=(event,offset)=>{const m=metrics();moveView(axis,Math.max(1,Math.min(m.max,1+Math.round((point(event)-m.origin-offset)/m.travel*(m.max-1)))));};
    const down=event=>{if(event.button!==0||track.getAttribute('aria-disabled')==='true')return;event.preventDefault();track.focus({preventScroll:true});if(event.target===thumb){const r=thumb.getBoundingClientRect();dragging=point(event)-(vertical?r.top:r.left);track.setPointerCapture(event.pointerId);}else move(event,metrics().size/2);};
    const pointermove=event=>{if(dragging!==null)move(event,dragging);};
    const up=event=>{dragging=null;if(track.hasPointerCapture(event.pointerId))track.releasePointerCapture(event.pointerId);};
    const key=event=>{if(event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;const current=vertical?firstRow:firstCol,count=vertical?rowCount:colCount,m=metrics();let value;if(event.key==='Home')value=1;else if(event.key==='End')value=m.max;else if(event.key==='PageDown')value=current+count;else if(event.key==='PageUp')value=current-count;else if(event.key===(vertical?'ArrowDown':'ArrowRight'))value=current+1;else if(event.key===(vertical?'ArrowUp':'ArrowLeft'))value=current-1;else return;event.preventDefault();event.stopPropagation();moveView(axis,Math.max(1,Math.min(m.max,value)));};
    track.addEventListener('pointerdown',down);track.addEventListener('pointermove',pointermove);track.addEventListener('pointerup',up);track.addEventListener('pointercancel',up);track.addEventListener('keydown',key);
    cleanup.push(()=>{track.removeEventListener('pointerdown',down);track.removeEventListener('pointermove',pointermove);track.removeEventListener('pointerup',up);track.removeEventListener('pointercancel',up);track.removeEventListener('keydown',key);});
  }
  previous.onclick=()=>{tabs.scrollLeft-=tabs.clientWidth*.75;syncTabs();};next.onclick=()=>{tabs.scrollLeft+=tabs.clientWidth*.75;syncTabs();};tabs.addEventListener('scroll',syncTabs);
  const tabKeys=event=>{if(!['ArrowLeft','ArrowRight'].includes(event.key)||event.altKey||event.ctrlKey||event.metaKey)return;event.preventDefault();const index=names.indexOf(active),nextIndex=(index+(event.key==='ArrowRight'?1:-1)+names.length)%names.length;switchSheet(names[nextIndex]);tabs.children[nextIndex].focus({preventScroll:true});};tabs.addEventListener('keydown',tabKeys);
  const resize=new ResizeObserver(()=>{const count=root.clientWidth<950?5:6;if(count!==colCount){colCount=count;reveal();render();}else{syncBar('vertical');syncBar('horizontal');syncTabs();}});resize.observe(root);
  const excludeMobile=()=>{if(!desktop.matches)root.replaceChildren(node('p','Source inspection is available on desktop.'));};desktop.addEventListener('change',excludeMobile);
  reveal();render();
  return()=>{resize.disconnect();desktop.removeEventListener('change',excludeMobile);cleanup.forEach(f=>f());table.removeEventListener('click',click);table.removeEventListener('keydown',keydown);nameBox.removeEventListener('keydown',jump);tabs.removeEventListener('scroll',syncTabs);tabs.removeEventListener('keydown',tabKeys);};
}
