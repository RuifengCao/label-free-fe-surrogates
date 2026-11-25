"""The day of the stamp of gate G-F2.1, in UTC, as the integer YYYYMMDD: the seed of the gate's sample.

Written when the stamp is prepared, and part of the hashed configuration (f21/config.py) and of the stamped code.
The stamp is the commit that adds docs/G-F2.1_code.sha256. If that commit carries another day as its committer date
in UTC, the stamp is void: nothing is drawn, and the stamp is made again with that day here. If the day of the
stamp is among the seeds that drew members of the family before the stamp (f21/config.py), the seed is the first
later day that is not, and docs/PRESPEC_G-F2.1.md says so.
"""
SAMPLE_SEED = 20261125
