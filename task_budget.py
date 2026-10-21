"""Optional process-safe task spending ledger. Unknown requests retain reservations."""
import fcntl
import json
import os
from pathlib import Path
import uuid
from engine import InputError


def update(amount=None, ticket=None, cost=None, metadata=None):
    path=os.environ.get('COPILOT_TASK_BUDGET_FILE')
    if not path:return None
    path=Path(path)
    if path.is_symlink():raise InputError('Task budget ledger must not be a symlink.')
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    from ai_runtime import positive
    ceiling=positive(os.environ.get('COPILOT_TASK_BUDGET_USD'),'Task budget ceiling')
    # Separate lock survives atomic ledger replacement and serializes processes.
    with open(str(path)+'.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:
            ledger=json.loads(path.read_text()) if path.exists() else dict(ceiling_usd=ceiling,requests={})
            if ledger['ceiling_usd']!=ceiling:raise InputError('Task budget ceiling differs from existing authorization ledger.')
            if amount is not None:
                amount=positive(amount,'Request reservation')
                if sum(x['committed_usd'] for x in ledger['requests'].values())+amount>ceiling:raise InputError('Task API spending ceiling reached; no request sent.')
                ticket=uuid.uuid4().hex
                ledger['requests'][ticket]=dict(committed_usd=amount,reserved_usd=amount,status='reserved',**(metadata or {}))
            elif ticket:
                row=ledger['requests'][ticket]
                if not isinstance(cost,(int,float)) or not 0<=cost<=row['reserved_usd']:raise InputError('Invalid task budget settlement; reservation retained.')
                row.update(committed_usd=cost,estimated_usd=cost,status='settled')
            ledger['committed_usd']=sum(x['committed_usd'] for x in ledger['requests'].values())
            temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
            try:
                with open(temporary,'x') as out:
                    os.chmod(temporary,0o600);json.dump(ledger,out,indent=2);out.flush();os.fsync(out.fileno())
                os.replace(temporary,path)
            finally:
                temporary.unlink(missing_ok=True)
            return ticket
        except InputError:
            raise
        except (ValueError,KeyError,TypeError) as exc:
            raise InputError('Task budget ledger invalid; no spending authorized.') from exc
