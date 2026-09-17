# Add a reversible feature toggle across stored records

The feature is disabled by default. With it off, preserve legacy writes and
reads. With it on, store and return the derived value. Turning it off again must
not reinterpret existing records. Change only `rollout/feature.py`.
