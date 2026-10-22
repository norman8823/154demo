export default function ({parentElement, data}) {
  const root = parentElement.querySelector('.excel-viewer');
  // Component-owned nodes only; workbook strings always use textContent/value.
  const node = (tag, text, className) => {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  const letters = column => {
    let result = '';
    while (column > 0) {column--; result = String.fromCharCode(65 + column % 26) + result; column = Math.floor(column / 26);}
    return result;
  };
  const parse = value => {
    const match = /^([A-Z]{1,3})([1-9]\d*)$/.exec(value.trim().toUpperCase());
    if (!match) return null;
    const col = [...match[1]].reduce((n, c) => n * 26 + c.charCodeAt(0) - 64, 0);
    const row = Number(match[2]);
    return row <= data.rows && col <= data.columns ? [row, col] : null;
  };
  let [row, col] = parse(data.initial);
  let rowCount = 12, colCount = 4;
  let firstRow = Math.max(1, row - 5), firstCol = Math.max(1, col - 2);
  const coord = () => letters(col) + row;
  const toolbar = node('div', undefined, 'formula-toolbar');
  const nameBox = node('input', undefined, 'name-box');
  nameBox.setAttribute('aria-label', 'Selected cell');
  nameBox.setAttribute('title', 'Selected coordinate. Enter a coordinate and press Enter to navigate.');
  nameBox.setAttribute('spellcheck','false');
  const fx = node('span', 'ƒx', 'fx'); fx.setAttribute('aria-hidden','true');
  const formula = node('output', undefined, 'formula-bar');
  formula.setAttribute('aria-label','Original formula or raw value');
  formula.tabIndex = 0;
  toolbar.append(nameBox,fx,formula);
  const hint = node('p','Read-only · Click a cell; use arrow keys while the grid has focus.','grid-hint');
  const status = node('p', '', 'grid-status');status.setAttribute('role','status');
  const range = node('p', undefined, 'grid-range');
  const table = node('table', undefined, 'source-grid');
  table.setAttribute('role','grid');table.setAttribute('aria-readonly','true');
  table.setAttribute('aria-label', data.sheet + ' original worksheet');
  table.setAttribute('aria-rowcount',data.rows + 1);table.setAttribute('aria-colcount',data.columns + 1);
  const nav = node('div', undefined, 'range-navigation');
  const buttons = [];
  const addButton = (label, dr, dc) => {
    const button = node('button',label);
    button.type='button';
    button.onclick=() => select(Math.min(data.rows,Math.max(1,row+dr*rowCount)),Math.min(data.columns,Math.max(1,col+dc*colCount)),false);
    nav.append(button);buttons.push({button,dr,dc});
  };
  addButton('↑ Rows',-1,0); addButton('↓ Rows',1,0);addButton('← Columns',0,-1);addButton('Columns →',0,1);
  const details = node('details',undefined,'source-details');
  const summary = node('summary','Cell provenance & original units');
  const provenance = node('dl');details.append(summary,provenance);
  root.replaceChildren(toolbar,hint,status,range,table,nav,details);

  function updateDetails(record) {
    const fields = [
      ['Source coordinate', data.sheet + ' · ' + coord()],
      ['Source label', record.label || 'No row label recorded'],
      ['Original observed value', record.observed ?? '(blank)'],
      ['Value provenance', record.origin || 'Original workbook blank cell'],
      ['Original number format', record.format || 'General'],
    ];
    if (record.standardized !== undefined && record.standardized !== '') {
      fields.push(['Source-unit multiplier', record.scale || 'Not recorded'],
        ['Verified standardized value',record.standardized + ' ' + record.currency],
        ['Reported period',record.period || 'Not recorded']);
    }
    if (record.comment) fields.push(['Original cell comment',record.comment]);
    provenance.replaceChildren(...fields.flatMap(([label,value])=>[node('dt',label),node('dd',value)]));
  }
  function render(focus) {
    const selected = coord();
    const record = data.cells[selected] || {};
    nameBox.value = selected;
    formula.textContent = record.bar ?? '';
    formula.setAttribute('data-coordinate', selected);
    updateDetails(record);
    // Keep the visible range bounded; selected cells always stay in view.
    if (row < firstRow) firstRow=row;
    if (row >= firstRow+rowCount) firstRow=row-rowCount+1;
    if (col < firstCol) firstCol=col;
    if (col >= firstCol+colCount) firstCol=col-colCount+1;
    firstRow=Math.max(1,Math.min(firstRow,Math.max(1,data.rows-rowCount+1)));
    firstCol=Math.max(1,Math.min(firstCol,Math.max(1,data.columns-colCount+1)));
    const lastRow=Math.min(data.rows,firstRow+rowCount-1), lastCol=Math.min(data.columns,firstCol+colCount-1);
    range.textContent=data.sheet+' · '+letters(firstCol)+firstRow+':'+letters(lastCol)+lastRow+' · '+data.rows+' rows × '+data.columns+' columns';
    const head=node('thead'),header=node('tr');header.setAttribute('role','row');
    header.append(node('th',''));
    for(let c=firstCol;c<=lastCol;c++) {
      const th=node('th',letters(c),c===col?'selected-header':'');
      th.setAttribute('scope','col');th.setAttribute('role','columnheader');header.append(th);
    }
    head.append(header);
    const body=node('tbody');
    for(let r=firstRow;r<=lastRow;r++) {
      const tr=node('tr');tr.setAttribute('role','row');tr.setAttribute('aria-rowindex',r+1);
      const th=node('th',String(r),r===row?'selected-header':'');
      th.setAttribute('scope','row');th.setAttribute('role','rowheader');tr.append(th);
      for(let c=firstCol;c<=lastCol;c++) {
        const address=letters(c)+r,cell=data.cells[address] || {};
        const td=node('td',cell.display ?? '',cell.bold?'source-bold':'');
        td.setAttribute('role','gridcell');td.setAttribute('data-coordinate',address);
        td.setAttribute('aria-colindex',c+1);td.setAttribute('aria-label',address+': '+(cell.display ?? '(blank)'));
        const active=address===selected;
        td.setAttribute('aria-selected',String(active));td.tabIndex=active?0:-1;
        if(active) td.classList.add('source-target');
        td.title=address;tr.append(td);
      }
      body.append(tr);
    }
    table.replaceChildren(head,body);
    for(const {button,dr,dc} of buttons) button.disabled=(dr<0 && row===1)||(dr>0 && row===data.rows)||(dc<0 && col===1)||(dc>0 && col===data.columns);
    if(focus) table.querySelector('[aria-selected="true"]').focus({preventScroll:true});
  }
  function select(r,c,focus=true) {
    row=r;col=c;status.textContent='';render(focus);
  }
  const click = event => {
    const target=event.target.closest('[role="gridcell"]');
    if(!target) return;
    select(...parse(target.dataset.coordinate));
  };
  const keydown = event => {
    if(!event.target.closest('[role="gridcell"]') || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const delta={ArrowUp:[-1,0],ArrowDown:[1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]}[event.key];
    if(!delta) return;
    event.preventDefault();event.stopPropagation();
    select(Math.max(1,Math.min(data.rows,row+delta[0])),Math.max(1,Math.min(data.columns,col+delta[1])));
  };
  const jump = event => {
    if(event.key!=='Enter') return;
    event.preventDefault();
    const destination=parse(nameBox.value);
    if(destination) select(...destination);
    else {nameBox.value=coord();status.textContent='That coordinate is outside the original worksheet. Selection is unchanged.';}
  };
  nameBox.addEventListener('keydown',jump);
  nameBox.addEventListener('blur',()=>{nameBox.value=coord();});
  table.addEventListener('click',click);table.addEventListener('keydown',keydown);
  // A bounded viewport rather than an internally scrolling spreadsheet panel.
  const resize = new ResizeObserver(entries=>{
    const mobile=entries[0].contentRect.width<520;
    const nextRows=mobile?8:12,nextCols=mobile?2:4;
    if(nextRows!==rowCount || nextCols!==colCount) {rowCount=nextRows;colCount=nextCols;render(table.contains(parentElement.activeElement));}
  });
  resize.observe(root);
  render(false);
  return () => {resize.disconnect();table.removeEventListener('click',click);table.removeEventListener('keydown',keydown);nameBox.removeEventListener('keydown',jump);};
}
