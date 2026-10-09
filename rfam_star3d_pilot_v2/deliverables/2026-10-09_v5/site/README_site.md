# SQARMA website (v5, local only)

Regenerate the data from the active tables, then serve the folder:

```
cd rfam_star3d_pilot_v2
.venv/bin/python scripts/export_site_data.py
cd deliverables/2026-10-09_v5/site && ../../../.venv/bin/python -m http.server 8765    # open http://localhost:8765
```

Opening `index.html` directly from disk will not load the data; serve the folder over HTTP instead.
