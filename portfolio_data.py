"""Read-only GP adapter over the checkpoint's verified prepared Review contract.

No analysis entry point, credential loader, provider client or cache miss fallback
is used here. Verification includes the frozen app/report source hashes.
"""
from dataclasses import dataclass
from copy import deepcopy

from engine import Review, InputError
from report_cache import reused
from scripts.seed_demo_results import verify_prepared


@dataclass(frozen=True)
class Company:
    id: str
    name: str
    sector: str
    run: str
    review: Review
    provenance: dict


# Registry metadata only. All financial values/findings/periods come from Reviews.
REGISTRY = (
    ('summit', 'Summit Home Services', 'Residential home services', 'summit-05-final'),
    ('tallis', 'Tallis Brook Accounting', 'Accounting services', 'tallis-05-final'),
    ('harrow', 'Harrow Ridge Environmental', 'Environmental services', 'harrow-17-final'),
)


def load_companies():
    """Fail closed if a prepared source is missing, changed or unverifiable."""
    verified = {entry['run']: (entry, review) for entry, review, _ in verify_prepared()}
    companies = []
    for slug, name, sector, run in REGISTRY:
        if run not in verified:
            raise InputError('Verified prepared company is unavailable: ' + name)
        entry, original = verified[run]
        review = deepcopy(original)
        review.package['prepared_demo'] = dict(run=run, snapshot_sha256=entry['snapshot_sha256'], new_model_calls=0)
        reused(review, 'verified-portfolio-prepared')
        companies.append(Company(slug, name, sector, run, review, deepcopy(entry)))
    return tuple(companies)


def company_by_id(companies, slug):
    return next((c for c in companies if c.id == slug), None)
