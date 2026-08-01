# External-service cache

Runtime PubChem identity and structure caches are written here by default, or under `CACHE_DIR` when configured. Identity entries are keyed by normalized formula and charge. Structure entries are keyed by PubChem CID, record type, and format. Entries expire after `PUBCHEM_CACHE_TTL_SECONDS`; corrupt JSON is ignored safely and subsequent atomic writes rebuild it.

The directory contains reference data and computed structure text only—no API secrets or user profiles. PubChem requires no API key. Deployments should mount this directory writable if cross-request caching is desired; otherwise the application remains correct and simply fetches again when external lookup is enabled.
