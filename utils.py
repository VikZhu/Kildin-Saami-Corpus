import string

punct_base = string.punctuation + '«»—–−‐-‒–—―‖‗‘’‚‛“”„‟…'
punct = set(c for c in punct_base if c not in {"'", "’"}) 