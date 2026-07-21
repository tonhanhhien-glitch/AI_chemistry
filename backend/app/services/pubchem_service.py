"""Feature-flagged PubChem reference lookup with timeout and disk cache."""

from dataclasses import asdict, dataclass
import hashlib
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from app.core.config import settings
from app.utils.json_utils import read_json_cache, write_json_cache


@dataclass(frozen=True, slots=True)
class PubChemCandidate:
    cid: int
    molecular_formula: str
    canonical_smiles: str | None
    isomeric_smiles: str | None
    molecular_weight: str | None
    source: str = "PubChem reference"


def lookup_pubchem(query: str) -> list[PubChemCandidate]:
    if not settings.ENABLE_PUBCHEM:
        return []
    key = hashlib.sha256(query.strip().casefold().encode("utf-8")).hexdigest()
    cache_path = settings.CACHE_DIR / "pubchem_cache.json"
    cache = read_json_cache(cache_path)
    if isinstance(cache.get(key), list):
        try:
            return [PubChemCandidate(**item) for item in cache[key]]
        except (TypeError, ValueError):
            cache.pop(key, None)
    fields = "CID,MolecularFormula,CanonicalSMILES,IsomericSMILES,MolecularWeight"
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(query)}/property/{fields}/JSON"
    try:
        with urlopen(url, timeout=settings.PUBCHEM_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = payload.get("PropertyTable", {}).get("Properties", [])
        candidates = [PubChemCandidate(cid=int(row["CID"]), molecular_formula=str(row.get("MolecularFormula", "")), canonical_smiles=row.get("ConnectivitySMILES") or row.get("CanonicalSMILES"), isomeric_smiles=row.get("SMILES") or row.get("IsomericSMILES"), molecular_weight=str(row["MolecularWeight"]) if row.get("MolecularWeight") is not None else None) for row in rows]
        cache[key] = [asdict(candidate) for candidate in candidates]
        write_json_cache(cache_path, cache)
        return candidates
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, json.JSONDecodeError):
        return []
