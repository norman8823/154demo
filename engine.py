"""Bounded, local analysis of the three supported September reporting formats."""
import ast
import csv
import io
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries, get_column_letter

ROOT = Path(__file__).parent
DRAFT = 'DRAFT — Requires Investment Team Review'
BASIS = 'Platform A is accrual basis; Add-on B QuickBooks is cash basis. Revenue and EBITDA are not consolidated. Covenant figures are reported pro forma figures, not a cash-to-accrual reconciliation.'

class InputError(ValueError):
    pass

class MissingData(InputError):
    pass


NOT_AVAILABLE = 'Not available — additional data required.'
ANALYSES = {0:'Add-on B cash-basis summary', 1:'Profitability vs. management commentary', 2:'Covenant headroom', 3:'Potential billing leakage'}


class Book:
    """Evaluate the small arithmetic formula vocabulary used by these workbooks.

    Recompute supported formulas from source cells, never execute workbook code or
    rely on potentially stale Excel caches. Other formula types are rejected.
    """
    def __init__(self, name, data):
        self.name = name
        try:
            self.wb = load_workbook(io.BytesIO(data), data_only=False)
        except Exception as e:
            raise InputError(f'{name}: cannot open this .xlsx workbook.') from e
        self.strict_sum = True
        self.cache = {}
        self.active = set()

    def require(self, sheets):
        missing = set(sheets) - set(self.wb.sheetnames)
        if missing:
            raise InputError(f'{self.name}: missing sheets: {", ".join(sorted(missing))}.')

    def value(self, sheet, coord):
        if sheet not in self.wb.sheetnames:
            raise MissingData(f'{self.name}: missing sheet {sheet}.')
        key = (sheet, coord)
        if key in self.cache:
            return self.cache[key]
        if key in self.active:
            raise InputError(f'{self.name}: circular formula at {sheet}!{coord}.')
        self.active.add(key)
        try:
            raw = self.wb[sheet][coord].value
            result = self.formula(sheet, raw[1:]) if isinstance(raw, str) and raw.startswith('=') else raw
            self.cache[key] = result
            return result
        finally:
            self.active.remove(key)

    def formula(self, sheet, expr):
        refs = []
        pattern = r"(?:(?:'([^']+)'|([A-Za-z_][\w ]*))!)?(\$?[A-Z]{1,3}\$?\d+)(?::(\$?[A-Z]{1,3}\$?\d+))?"
        def sub(m):
            target = m[1] or m[2] or sheet
            start, end = m[3].replace('$',''), (m[4] or '').replace('$','')
            if end:
                a,b,c,d = range_boundaries(f'{start}:{end}')
                val = [self.value(target, f'{get_column_letter(x)}{y}') for y in range(b,d+1) for x in range(a,c+1)]
            else:
                val = self.value(target, start)
            refs.append(val)
            return f'R[{len(refs)-1}]'
        translated = re.sub(pattern, sub, expr)
        translated = re.sub(r'(?<![<>=!])=(?!=)', '==', translated)
        tree = ast.parse(translated, mode='eval')
        def ev(n):
            if isinstance(n, ast.Expression): return ev(n.body)
            if isinstance(n, ast.Constant): return n.value
            if isinstance(n, ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='R': return refs[ev(n.slice)]
            if isinstance(n, ast.UnaryOp):
                v=ev(n.operand)
                if isinstance(n.op, ast.USub): return -v
                if isinstance(n.op, ast.UAdd): return v
            if isinstance(n, ast.BinOp):
                a,b=ev(n.left),ev(n.right)
                if isinstance(n.op,ast.Add): return a+b
                if isinstance(n.op,ast.Sub): return a-b
                if isinstance(n.op,ast.Mult): return a*b
                if isinstance(n.op,ast.Div): return a/b
            if isinstance(n,ast.Compare) and len(n.ops)==1:
                a,b=ev(n.left),ev(n.comparators[0]); op=n.ops[0]
                if isinstance(op,ast.Eq): return a==b
                if isinstance(op,ast.Gt): return a>b
                if isinstance(op,ast.Lt): return a<b
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):
                name=n.func.id.upper()
                if name=='IF': return ev(n.args[1] if ev(n.args[0]) else n.args[2])
                args=[ev(a) for a in n.args]
                if name=='SUM':
                    values=[v for a in args for v in (a if isinstance(a,list) else [a])]
                    if not self.strict_sum: values=[v for v in values if v is not None]
                    if any(not isinstance(v,(int,float)) or isinstance(v,bool) for v in values):
                        raise InputError('A required financial SUM contains a blank or nonnumeric source value.')
                    return sum(values)
                if name=='ABS': return abs(args[0])
            raise InputError('Unsupported formula in supplied format; recalculate and use the supported workbook structure.')
        return ev(tree)

    def locate(self, sheet, label, col='A'):
        matches=[row for row in range(1,self.wb[sheet].max_row+1) if str(self.wb[sheet][f'{col}{row}'].value or '').strip()==label]
        if not matches: raise MissingData(f'{self.name}: required row {label!r} is missing from {sheet}.')
        if len(matches)!=1: raise InputError(f'{self.name}: mapping required; ambiguous {label!r} rows in {sheet}.')
        return matches[0]

    def number(self, sheet, coord):
        try: val=self.value(sheet,coord)
        except InputError: raise
        except Exception as e: raise InputError(f'{self.name}: cannot calculate {sheet}!{coord}. Check source values/formulas.') from e
        if not isinstance(val,(int,float)) or isinstance(val,bool) or not math.isfinite(val):
            raise InputError(f'{self.name}: {sheet}!{coord} must contain a valid number.')
        return val

@dataclass
class Review:
    metrics: dict = field(default_factory=dict)
    evidence: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    billing: list = field(default_factory=list)
    mapping: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    memo: str = ''
    questions: list = field(default_factory=list)
    recognized: list = field(default_factory=list)
    readiness: list = field(default_factory=list)
    adaptive: bool = False
    company: str = ''
    report_period: str = 'September 2026'
    basis_note: str = BASIS
    banner: str = 'SYNTHETIC DEMONSTRATION DATA'
    currency: str = 'USD'
    scale: float | None = 1
    normalized: list = field(default_factory=list)
    financial_rows: list = field(default_factory=list)
    narrative_mode: str = 'Deterministic draft · local / offline'
    package: dict = field(default_factory=dict)


def demo_files():
    return {p.name:p.read_bytes() for p in sorted((ROOT/'inputs').iterdir()) if p.suffix in ('.xlsx','.csv')}


def venue_key(value):
    # Only known straightforward venue suffixes are normalized; no fuzzy matching.
    m=re.fullmatch(r'venue\s*#?\s*0*(\d+)(?:\s*-\s*club level)?',value.strip(),re.I)
    return f'Venue {int(m[1])}' if m else value.strip().casefold()


def analyze_known(files):
    if not files: raise InputError('Upload at least one supported financial file, or choose Use Demo Files.')
    books=[]; csvs=[]
    for name,data in files.items():
        if name.lower().endswith('.xlsx'): books.append(Book(name,data))
        elif name.lower().endswith('.csv'): csvs.append((name,data))
        else: raise InputError(f'{name}: mapping required. Supported inputs are the known .xlsx reporting workbooks and schedule CSV.')
    platforms=[]; addons=[]
    for book in books:
        sheets=set(book.wb.sheetnames)
        platform=bool(sheets & {'P&L','Covenant','Operating KPIs','CEO Letter'})
        addon=bool(sheets & {'Profit and Loss','Rate Card','Payroll Summary'})
        if platform == addon:
            raise InputError(f'{book.name}: mapping required. Structure is unrecognized or ambiguous; use the supported Platform A or Add-on B workbook layout.')
        (platforms if platform else addons).append(book)
    if len(platforms)>1 or len(addons)>1 or len(csvs)>1:
        raise InputError('Multiple files match the same reporting type. Supply one workbook per company and one schedule CSV; combining duplicate reporting packages requires mapping.')
    p=platforms[0] if platforms else None
    q=addons[0] if addons else None
    r=Review(); m=r.metrics
    def fact(fid,book,sheet,coord,group,meaning):
        val=book.value(sheet,coord)
        raw=book.wb[sheet][coord].value
        r.evidence.append({'Fact ID':fid,'Finding':group,'File':book.name,'Reference':f"'{sheet}'!{coord}",'Original value / formula':raw,'Validated value':val,'Check / use':meaning})
        return val
    def num(fid,book,sheet,coord,group,meaning):
        val=book.number(sheet,coord); fact(fid,book,sheet,coord,group,meaning); return val
    for book in books:
        for sheet,coord,expected in [('P&L','A5','Line item'),('Covenant','A4','Item'),('Operating KPIs','A4','KPI'),('Profit and Loss','A3','Profit and Loss'),('Payroll Summary','A4','Pay month')]:
            if sheet in book.wb.sheetnames and book.wb[sheet][coord].value!=expected:
                raise InputError(f'{book.name}: mapping required for {sheet}; expected the supported header at {coord}.')
        kind='Platform A monthly package' if book is p else 'Add-on B QuickBooks package'
        r.recognized.append({'File':book.name,'Recognized as':kind})
        r.evidence.append({'Fact ID':f'input_{len(r.recognized)}','Finding':0,'File':book.name,'Reference':'Workbook sheet names and supported headers','Original value / formula':', '.join(book.wb.sheetnames),'Validated value':kind,'Check / use':'Recognized known reporting structure; run only checks with required data.'})

    def run_check(identifier,book,required,callback,additional):
        missing=[sheet for sheet in required if book is None or sheet not in book.wb.sheetnames]
        status={'Analysis ID':identifier,'Analysis':ANALYSES[identifier],'Status':'Available','Additional data':''}
        if missing:
            status.update(Status=NOT_AVAILABLE, **{'Additional data':additional+' Missing: '+', '.join(missing)+'.'})
        else:
            before=dict(m); evidence_count=len(r.evidence); mapping_count=len(r.mapping)
            try: callback()
            except MissingData as e:
                m.clear(); m.update(before); del r.evidence[evidence_count:]; del r.mapping[mapping_count:]
                status.update(Status=NOT_AVAILABLE, **{'Additional data':str(e)})
        r.readiness.append(status)

    def profitability():
        if 'Sep-26' not in str(p.wb['P&L']['B5'].value) or 'Budget' not in str(p.wb['P&L']['C5'].value):
            raise MissingData('Platform profitability requires the supported September actual and budget columns in P&L.')
        if p.wb['Operating KPIs']['M4'].value!='Sep-26':
            raise MissingData('Platform profitability requires the September Operating KPIs column.')
        if 'Accrual' not in str(p.wb['Cover']['A7'].value):
            raise InputError('Expected Platform A accrual basis label; please verify the reporting basis.')
        for key,label in [('revenue','Total Revenue'),('gross_profit','Gross Profit'),('subcontract','Subcontracted Labor')]:
            row=p.locate('P&L',label)
            for suffix,col in [('', 'B'),('_budget','C')]:
                m[key+suffix]=num(key+suffix,p,'P&L',f'{col}{row}',1,label+'; recompute source formula where present')
        if m['revenue']<=0 or m['revenue_budget']<=0: raise InputError('Platform revenue and budget must be positive.')
        # Known-layout extraction is an adapter. The common normalized financial
        # reducer supplies gross margin, exactly as for unfamiliar statements.
        from financial_analysis import aggregate
        for suffix in ('','_budget'):
            col='C' if suffix else 'B'
            cost_row=p.locate('P&L','Total Direct Costs')
            cogs=num('cogs'+suffix,p,'P&L',f'{col}{cost_row}',1,'Reported direct costs; normalized P&L category')
            rows=[]
            for category,key in [('revenue','revenue'),('cogs','cogs'),('gross_profit','gross_profit')]:
                value=cogs if category=='cogs' else m[key+suffix]
                source=next(e for e in r.evidence if e['Fact ID']==key+suffix)
                rows.append({'category':category,'role':'total','value':value,'label':category,'context':'','source_file':p.name,'source_ref':source['Reference'],'period':'2026-09','scenario':'budget' if suffix else 'actual'})
            values,_,checks,_=aggregate(rows)
            if checks:raise InputError('Platform gross profit does not reconcile to normalized revenue and direct costs.')
            r.normalized.extend(rows)
            m['gm'+suffix]=values['gm']

        m['gm_variance_pp']=(m['gm']-m['gm_budget'])*100
        m['revenue_variance']=m['revenue']/m['revenue_budget']-1
        m['subcontract_variance']=m['subcontract']-m['subcontract_budget']
        for key,label in [('gm','Gross Margin %')]:
            row=p.locate('P&L',label)
            for suffix,col in [('', 'B'),('_budget','C')]:
                source=num(key+suffix+'_source',p,'P&L',f'{col}{row}',1,'Cross-check gross profit / revenue')
                if abs(source-m[key+suffix])>1e-8: raise InputError('Gross margin does not reconcile to P&L totals.')
        for key,label in [('requested','Shifts requested'),('filled','Shifts filled'),('fill','Fill rate')]:
            row=p.locate('Operating KPIs',label)
            m[key]=num(key,p,'Operating KPIs',f'M{row}',1,'September event staffing only; patrol excluded')
        if m['requested']<=0 or abs(m['filled']/m['requested']-m['fill'])>1e-8: raise InputError('Fill rate does not reconcile to shifts.')
        ceo=[]
        for row in p.wb['CEO Letter']:
            for c in row:
                if isinstance(c.value,str) and ('fill rate' in c.value.lower() or 'gross margin' in c.value.lower()):
                    ceo.append(fact('ceo_claim',p,'CEO Letter',c.coordinate,1,'Compare management assertion with computed facts'))
        m['ceo_claim']=' '.join(ceo) or 'No explicit fill-rate / margin assertion found.'
        match=re.search(r'fill rate[^%]*?(\d+(?:\.\d+)?)%',m['ceo_claim'],re.I)
        m['ceo_fill']=float(match[1])/100 if match else None
    run_check(1,p,['Cover','P&L','Operating KPIs','CEO Letter'],profitability,'Upload the Platform A monthly package for margin, KPI and commentary comparisons.')

    def covenant():
        if p.wb['Covenant']['B4'].value!='Value':
            raise MissingData('Covenant analysis requires the supported Value column.')
        covenant_labels={'base_platform':'LTM Adjusted EBITDA (Platform A)','pre_acquisition':'Pro forma Add-on B EBITDA, pre-acquisition period (Oct-25 to May-26)','post_acquisition':'Add-on B EBITDA, post-acquisition (Jun-26 to Sep-26)','synergies':'Run-rate cost synergies','reported_ebitda':'Covenant EBITDA (as reported)','net_debt':'Net debt','leverage_reported':'Net leverage (as reported)','covenant_max':'Maximum permitted','synergy_cap':'Synergy add-back cap, % of covenant EBITDA before synergies'}
        for key,label in covenant_labels.items():
            row=p.locate('Covenant',label)
            m[key]=num(key,p,'Covenant',f'B{row}',2,label)
        row=p.locate('Covenant','Maximum permitted')
        note=str(fact('stepdown_terms',p,'Covenant',f'C{row}',2,'Future threshold only; no forecast of breach'))
        step=re.search(r'(\d+(?:\.\d+)?)x at (Mar-27)',note)
        if not step: raise InputError('Expected March 2027 covenant step-down in Covenant terms.')
        m['future_max']=float(step[1]); m['before_synergies']=m['base_platform']+m['pre_acquisition']+m['post_acquisition']
        if m['before_synergies']<=0 or not 0<=m['synergy_cap']<=1 or m['synergies']<0: raise InputError('Covenant base EBITDA must be positive and the synergy cap valid.')
        m['allowed_synergies']=min(m['synergies'],m['before_synergies']*m['synergy_cap'])
        m['synergy_trim']=m['synergies']-m['allowed_synergies']
        m['cap_ebitda']=m['before_synergies']+m['allowed_synergies']
        m['leverage_cap']=m['net_debt']/m['cap_ebitda']
        m['headroom_reported']=m['covenant_max']-m['leverage_reported']
        m['headroom_cap']=m['covenant_max']-m['leverage_cap']
        m['future_headroom']=m['future_max']-m['leverage_cap']
        if abs(m['reported_ebitda']-(m['before_synergies']+m['synergies']))>.01 or abs(m['leverage_reported']-m['net_debt']/m['reported_ebitda'])>1e-8:
            raise InputError('Reported covenant EBITDA / leverage does not reconcile.')
    run_check(2,p,['Covenant'],covenant,'Upload Platform A covenant terms and its supporting EBITDA / debt schedules.')

    def addon_summary():
        if q.wb['Profit and Loss']['E7'].value!='Sep 2026':
            raise MissingData('Add-on B summary requires the supported September column in Profit and Loss.')
        if 'Cash Basis' not in str(q.wb['Profit and Loss']['A5'].value):
            raise InputError('Expected Add-on B cash basis label; please verify the reporting basis.')
        m['addon_cash_income']=num('addon_cash_income',q,'Profit and Loss',f"E{q.locate('Profit and Loss','Total Income')}",0,'Cash basis total income; shown separately, no consolidation')
        for account,meaning in [('Contract Labor','Direct / subcontracted labor; reclassification may affect gross margin, not EBITDA if costs unchanged.'),('Customer Deposits','Potential deferred revenue review; timing and support required before any adjustment.'),('Ask My Accountant','Unmapped; controller classification required.')]:
            coord=f"E{q.locate('Profit and Loss',account)}"
            val=num('mapping_'+account,q,'Profit and Loss',coord,0,meaning)
            r.mapping.append({'Source account':account,'September ($)':val,'Proposed treatment':meaning,'Source':f'{q.name} · Profit and Loss!{coord}'})
    if q:
        run_check(0,q,['Profit and Loss'],addon_summary,'Add the Add-on B cash-basis Profit and Loss sheet for a separate income summary and mapping preview.')

    rates={}
    if q and 'Rate Card' in q.wb.sheetnames:
        try: header=q.locate('Rate Card','Venue')
        except MissingData as e: raise InputError(f'{q.name}: mapping required; expected the supported Rate Card headers.') from e
        if [q.wb['Rate Card'].cell(header,c).value for c in range(1,4)]!=['Venue','Position','Contract bill rate']:
            raise InputError('Mapping required: Rate Card columns must be Venue, Position, Contract bill rate.')
        for row in range(header+1,q.wb['Rate Card'].max_row+1):
            v,pos=q.wb['Rate Card'].cell(row,1).value,q.wb['Rate Card'].cell(row,2).value
            if not v: continue
            if not isinstance(pos,str): raise InputError('Missing rate-card position.')
            key=(venue_key(str(v)),pos.strip().casefold())
            if key in rates: raise InputError(f'Ambiguous duplicate contract rate for {v} / {pos}.')
            rate=q.number('Rate Card',f'C{row}')
            if rate<0: raise InputError('Contract rates must be nonnegative.')
            rates[key]=(rate,f'C{row}')
    billing_available=bool(rates and csvs)
    schedule_missing=[]
    if csvs:
        name,data=csvs[0]
        try: lines=data.decode('utf-8-sig').splitlines(keepends=True)
        except UnicodeDecodeError as e: raise InputError('Schedule CSV must use UTF-8 encoding.') from e
        offset=1 if lines and lines[0].startswith('#') else 0
        reader=csv.DictReader(io.StringIO(''.join(lines[offset:])))
        required=['Event ID','Venue','Position','Worked Hours','Bill Rate','Invoice #']
        if not reader.fieldnames or not {'Event ID','Venue','Position'}<=set(reader.fieldnames) or len(set(reader.fieldnames))!=len(reader.fieldnames):
            raise InputError(f'{name}: mapping required. Schedule CSV needs the supported event, venue, position, hours, rate and invoice columns.')
        schedule_missing=[column for column in required if column not in reader.fieldnames]
        billing_available=billing_available and not schedule_missing
        r.recognized.append({'File':name,'Recognized as':'Add-on B scheduling / invoice CSV'})
        seen=set(); duplicates=[]; unmatched=[]; count=0
        for row in reader:
            physical=offset+reader.line_num
            if None in row or any(v is None for v in row.values()): raise InputError(f'Schedule CSV row {physical}: malformed columns.')
            exact=tuple(row.values())
            if exact in seen: duplicates.append(physical); continue
            seen.add(exact); count+=1
            if schedule_missing: continue
            try: hours,rate=float(row['Worked Hours']),float(row['Bill Rate'])
            except ValueError as e: raise InputError(f'Schedule CSV row {physical}: invalid hours or bill rate.') from e
            if not all(math.isfinite(v) and v>=0 for v in (hours,rate)): raise InputError(f'Schedule CSV row {physical}: hours and rate must be finite and nonnegative.')
            if not billing_available: continue
            contract=rates.get((venue_key(row['Venue']),row['Position'].strip().casefold()))
            if not contract: unmatched.append(physical); continue
            price,ref=contract
            invoice=row['Invoice #'].strip()
            kind='Uninvoiced worked hours' if hours>0 and not invoice else ('Below contract rate' if invoice and hours>0 and rate<price else None)
            if not kind: continue
            value=round(hours*price if not invoice else hours*(price-rate),2)
            item={'CSV row':physical,'Event ID':row['Event ID'],'Venue':row['Venue'],'Canonical venue':venue_key(row['Venue']),'Position':row['Position'],'Worked hours':hours,'Invoice':invoice or '(blank)','Billed rate ($/h)':rate,'Contract rate ($/h)':price,'Exception':kind,'Potential value ($)':value,'Rate reference':f'{q.name} · Rate Card!{ref}'}
            r.billing.append(item)
            r.evidence.append({'Fact ID':f'billing_{physical}','Finding':3,'File':name,'Reference':f'CSV physical row {physical}','Original value / formula':str(row),'Validated value':value,'Check / use':f'{kind}: {hours} × '+(str(price) if not invoice else f'({price} − {rate})')+f'; contract {q.name}, Rate Card!{ref}; venue {venue_key(row["Venue"])}'})
            fact(f'rate_{physical}',q,'Rate Card',ref,3,'Contract rate for '+row['Venue']+' / '+row['Position'])
        if not count: raise InputError('Schedule CSV contains no data rows.')
        r.evidence.append({'Fact ID':'billing_scope','Finding':3 if billing_available else 0,'File':name,'Reference':f'CSV header row {offset+1}; data through physical row {offset+reader.line_num}', 'Original value / formula':f'{count} unique rows; {len(duplicates)} exact duplicates; {len(unmatched)} unmatched rates', 'Validated value':len(r.billing) if billing_available else 'Not valued', 'Check / use':'Match known venue variants + position to Rate Card; quantify disjoint uninvoiced / invoiced-rate exceptions only.' if billing_available else 'Schedule recognized; required schedule columns and contract rate card needed before financial valuation.'})
        m['duplicates_removed']=len(duplicates); m['schedule_rows']=count
        if duplicates: r.warnings.append('Exact duplicate CSV rows removed: '+', '.join(map(str,duplicates))+'. Multi-position event IDs retained.')
        if unmatched: r.warnings.append('No exact supported venue + position rate match for CSV rows '+', '.join(map(str,unmatched))+'. These rows are excluded from valuation.')
        if billing_available:
            m['unbilled']=round(sum(x['Potential value ($)'] for x in r.billing if x['Exception']=='Uninvoiced worked hours'),2)
            m['underbilled']=round(sum(x['Potential value ($)'] for x in r.billing if x['Exception']=='Below contract rate'),2)
            m['billing_total']=round(m['unbilled']+m['underbilled'],2)
    needed=[]
    if not csvs: needed.append('Add-on B scheduling / invoice CSV (worked hours, venue, position, billed rate and invoice number)')
    if schedule_missing: needed.append('Schedule columns: '+', '.join(schedule_missing))
    if not rates: needed.append('Add-on B Rate Card with populated venue + position contract rates')
    r.readiness.append({'Analysis ID':3,'Analysis':ANALYSES[3],'Status':'Available' if billing_available else NOT_AVAILABLE,'Additional data':'; '.join(needed)})
    return narratives(r)


def narratives(r):
    m=r.metrics
    available={row['Analysis ID'] for row in r.readiness if row['Status']=='Available'}
    questions=['Why do fill rate and gross margin differ from management commentary and budget, and what explains subcontract labor pressure?','What documentation supports the permitted synergy add-back, and what is the plan for the March covenant step-down?','Can the controller reconcile the flagged worked hours and below-contract rates to invoices, credits and contract amendments?']
    paragraphs=[]
    if 1 in available:
        claim=f"CEO states {m['ceo_fill']:.1%} fill rate" if m['ceo_fill'] is not None else 'CEO assertion requires manual review'
        f1=f"Gross margin {m['gm']:.1%} vs. {m['gm_budget']:.1%} budget ({m['gm_variance_pp']:+.2f} pp). Fill rate {m['fill']:.1%}; {claim}. Subcontract labor ${m['subcontract_variance']:,.0f} above budget."
        margin_alert=m['gm']<m['gm_budget']
        r.findings.append(dict(id=1,title='Profitability is deteriorating' if margin_alert else 'Profitability vs. management commentary',severity='HIGH PRIORITY' if margin_alert else 'REVIEW',indicator=f"{m['gm']:.1%}",unit='gross margin',summary=f1,calculation=f"Gross profit / revenue; actual {m['gross_profit']:,.0f} / {m['revenue']:,.0f}. Actual minus budget = {m['gm_variance_pp']:+.2f} percentage points.",conclusion='Margin below plan; management follow-up required.' if margin_alert else 'Margin meets or exceeds plan; reconcile commentary and operational KPIs.',caveat='Labor pressure and lower shift fill may be related; causation is not established. KPIs cover event staffing only.',action=questions[0]))
        paragraphs.append(f"Platform A reported ${m['revenue']:,.0f} September revenue ({m['revenue_variance']:+.1%} vs. budget). {f1} Labor pressure warrants management follow-up; causation is unverified.")
    if 2 in available:
        f2=f"Cap-only leverage {m['leverage_cap']:.2f}x vs. {m['leverage_reported']:.2f}x reported. Applying the {m['synergy_cap']:.0%} cap trims synergies by ${m['synergy_trim']:,.0f}; current maximum {m['covenant_max']:.2f}x, March 2027 maximum {m['future_max']:.2f}x."
        r.findings.append(dict(id=2,title='Covenant headroom needs review',severity='HIGH PRIORITY',indicator=f"{m['leverage_cap']:.2f}x",unit='cap-only sensitivity',summary=f2,calculation=f"Before-synergy EBITDA = ${m['before_synergies']:,.0f}. Allowed synergy = min(${m['synergies']:,.0f}, {m['synergy_cap']:.0%} × ${m['before_synergies']:,.0f}) = ${m['allowed_synergies']:,.2f}. Net debt ${m['net_debt']:,.0f} / capped EBITDA ${m['cap_ebitda']:,.2f} = {m['leverage_cap']:.4f}x.",conclusion='Reconcile permitted add-backs and prepare for the step-down.',caveat='Illustrative cap-only sensitivity, not a compliance certificate. Other add-backs held unchanged; no forecast or assertion of a future breach.',action=questions[1]))
        paragraphs.append(f2+' This is an illustrative sensitivity, not a compliance certificate.')
    if 3 in available:
        f3=f"${m['billing_total']:,.2f} potential billing exceptions: ${m['unbilled']:,.2f} uninvoiced worked hours and ${m['underbilled']:,.2f} invoiced rate differences. Reconcile to invoices before recognizing any recovery."
        r.findings.append(dict(id=3,title='Potential revenue leakage',severity='VERIFY WITH CFO',indicator=f"${m['billing_total']/1000:,.1f}K",unit='requiring reconciliation',summary=f3,calculation='Exact duplicate rows removed before venue + position matching. Uninvoiced = worked hours × contract rate. Invoiced only = worked hours × positive (contract − billed rate). The two groups are disjoint.',conclusion='An invoice-level check may identify recoverable revenue or data errors.',caveat='Potential exceptions, not proven loss or recovered revenue. Verify invoice status, credits, timing, and contract amendments; no cash/accrual adjustment inferred.',action=questions[2]))
        paragraphs.append(f3)
    if 'addon_cash_income' in m and not {1,2,3}<=available:
        paragraphs.append(f"Add-on B September cash-basis total income is ${m['addon_cash_income']:,.0f}, shown separately. This summary alone does not establish billing leakage or platform performance.")
    r.questions=[questions[f['id']-1] for f in r.findings]
    if not r.findings:
        paragraphs.append('No priority analyses could be completed with the available data. This is not a conclusion that there are no financial exceptions.')
    for status in r.readiness:
        if status['Status']!= 'Available': paragraphs.append(status['Analysis']+': '+NOT_AVAILABLE+' '+status['Additional data'])
    paragraphs.append(BASIS)
    r.memo=' '.join(paragraphs)
    return r


def company_name(review):
    if review.company: return review.company
    platform=any(x['Recognized as'].startswith('Platform A') for x in review.recognized)
    addon=any(x['Recognized as'].startswith('Add-on B') for x in review.recognized)
    return ' & '.join(name for name,present in [('Platform A',platform),('Add-on B',addon)] if present)


def is_known_package(files):
    """Exact known adapter signature, not a filename or mere sheet-name match."""
    if not files:return False
    for name,data in files.items():
        if name.lower().endswith('.csv'):
            try: header=next(csv.reader([line for line in data.decode('utf-8-sig').splitlines() if not line.startswith('#')]))
            except (UnicodeError,StopIteration):return False
            if not {'Event ID','Venue','Position'}<=set(header):return False
            continue
        if not name.lower().endswith('.xlsx'):return False
        b=Book(name,data);w=b.wb
        platform='P&L' in w.sheetnames and w['P&L']['A5'].value=='Line item' and w['P&L']['B5'].value=='Sep-26 Actual' and 'SYNTHETIC' in str(w['P&L']['A1'].value)
        addon=('Rate Card' in w.sheetnames and 'Profit and Loss' not in w.sheetnames) or ('Profit and Loss' in w.sheetnames and w['Profit and Loss']['A3'].value=='Profit and Loss' and w['Profit and Loss']['E7'].value=='Sep 2026' and w['Profit and Loss']['A2'].value=='Example Crowd Management Co')
        # Partial demo sheets still select their existing guarded specialized adapter.
        platform=platform or ('Covenant' in w.sheetnames and w['Covenant']['A4'].value=='Item' and str(w['Covenant']['A2'].value).startswith('Platform A:'))
        if not platform and not addon:return False
    return True


def partition_files(files):
    known={};general={}
    for name,data in files.items():
        (known if is_known_package({name:data}) else general)[name]=data
    return known,general


def _analyze_financials(files,decisions=None,layouts=None,profiles=None):
    if not files:raise InputError('Upload at least one financial workbook or CSV.')
    known,general=partition_files(files)
    if not general:return analyze_known(known)
    from ingestion import inspect_files,apply_decisions,MappingRequired
    from financial_analysis import analyze_intake
    intake=inspect_files(general,profiles=profiles,layouts=layouts)
    apply_decisions(intake,decisions or {})
    from mapping_ai import automate
    intake=automate(intake,general,profiles,layouts,decisions)
    try:result=analyze_intake(intake)
    except MappingRequired:
        if not known:raise
        result=analyze_known(known)
        result.warnings.append('Some additional files have no usable dated financial statement and were not analyzed: '+', '.join(general)+'. The supported package remains available.')
        result.memo+=' Data-quality limitation: '+result.warnings[-1]
        result.readiness.append({'Analysis ID':'unrecognized_inputs','Analysis':'Additional uploaded statements','Status':NOT_AVAILABLE,'Additional data':'Select a usable financial table and dated source columns for '+', '.join(general)})
        return result
    if known:
        specialized=analyze_known(known)
        result.findings.extend(specialized.findings)
        result.questions.extend(specialized.questions)
        result.evidence.extend([dict(e,**{'Fact ID':'known_'+e['Fact ID']}) for e in specialized.evidence])
        result.normalized.extend(specialized.normalized)
        result.recognized.extend(specialized.recognized)
        available={item['Analysis ID'] for item in specialized.readiness if item['Status']=='Available'}
        if 2 in available:result.readiness=[x for x in result.readiness if not x['Analysis'].endswith('Covenant sensitivity')]
        if 3 in available:result.readiness=[x for x in result.readiness if not x['Analysis'].endswith('Billing exceptions')]
        result.readiness.extend(specialized.readiness)
        result.warnings.extend(specialized.warnings)
        for key in ['revenue','gross_profit','gm','leverage_reported','leverage_cap','billing_total','addon_cash_income']:
            if key in specialized.metrics:
                result.financial_rows.append([company_name(specialized)+' · September 2026 · '+key,specialized.metrics[key],'ratio' if key=='gm' else ('multiple' if key.startswith('leverage') else 'USD'),'Known-package adapter; separate company / reporting basis','; '.join(e['Fact ID'] for e in result.evidence if e['Fact ID'].startswith('known_'))])
        if any(key in specialized.metrics for key in ['revenue','addon_cash_income']):
            result.company+=' & '+company_name(specialized)
            result.metrics={}  # No ambiguous cross-company headline/template metric.
            result.currency='unknown';result.scale=None
        if specialized.findings:result.memo+=' '+specialized.memo
        if any(key in specialized.metrics for key in ['revenue','addon_cash_income','billing_total','leverage_reported']) and result.report_period!='September 2026':result.report_period='Multiple reporting periods'
        result.basis_note+=' '+specialized.basis_note
    return result


def _analyze_package(files,decisions=None,layouts=None,profiles=None):
    from package_reader import read_package
    from package_analysis import enhance
    from ingestion import MappingRequired
    package=read_package(files)
    from ai_runtime import permitted
    if permitted() and __import__('os').environ.get('OPENAI_API_KEY'):
        from ai_evidence import grid_facts
        package['grid_facts'],notes=grid_facts(files);package['limitations'].extend(notes)
    try:review=_analyze_financials(files,decisions,layouts,profiles)
    except MappingRequired:
        if not package['series'] and not any(a['valid'] for a in package['aging']):raise
        review=Review(adaptive=True,currency='unknown',scale=None)
        review.company=' & '.join(dict.fromkeys(s['company'] for s in package['series']))
        periods=sorted({f['period'] for f in package['facts'] if f['period']})
        if periods:
            import calendar
            review.report_period=__import__('ingestion').period_label(periods[-1])
        review.warnings.append('No supported financial statement was recognized; only supporting schedules are analyzed.')
        review.basis_note='Supporting schedules are shown in their stated units; no income statement or consolidated headline was inferred.'
    package['_input_files']=files
    result=enhance(review,package)
    result.package.pop('_input_files',None)
    from company_context import ensure_context
    ensure_context(result,files)
    return result


def analyze(files,decisions=None,layouts=None,profiles=None,*,ai_authorized=False,ai_spend_limit=None,engine_name=None):
    from skill_engine import selected_engine
    chosen=engine_name or selected_engine()
    if chosen not in {'legacy','skill'}:raise InputError('Unknown analytical engine.')
    if chosen=='skill':
        from skill_engine import run
        return run(files,decisions,layouts,profiles,ai_authorized=ai_authorized,ai_spend_limit=ai_spend_limit)
    from ai_runtime import inference_session
    import json,logging
    with inference_session(ai_authorized,ai_spend_limit) as session:
        review=_analyze_package(files,decisions,layouts,profiles)
        review.package['engine_identity']='legacy'
        review.package['inference']=session.summary()
        from investigation import investigate
        investigate(review,files)
        review.package['inference']=session.summary()
        review.package['financial_extraction']=dict(normalized_records=len(review.normalized),unaccepted_records=sum(not row.get('accepted',False) for row in review.normalized),unknown_basis=any(row.get('basis','unknown')=='unknown' for row in review.normalized),readiness=review.readiness)
        review.narrative_mode=review.package.get('mode','Limited offline analysis — no accepted model assessment.')
        if review.package.get('ai_briefing') and not review.package['inference']['inference_observed']:
            review.narrative_mode='Mocked AI analysis — offline validation, not observed provider inference.'
        from ai_runtime import persist_diagnostics
        persist_diagnostics(review)
        logging.getLogger('copilot.inference').warning('copilot_review %s',json.dumps(review.package['inference'],separators=(',',':')))
        return review
