import re
from difflib import SequenceMatcher
THRESHOLD = 70

def norm(value):
    return ' '.join(str(value or '').lower().split())

def similarity(a, b):
    a,b=norm(a),norm(b)
    if not a or not b: return None
    wa,wb=set(re.findall(r'\w+',a)),set(re.findall(r'\w+',b))
    overlap=len(wa&wb)/len(wa|wb) if wa|wb else 0
    return max(SequenceMatcher(None,a,b).ratio(),overlap)

def score(a,b):
    if {norm(a.get('type')),norm(b.get('type'))}!={'lost','found'}: return None
    fields=[('itemName',0.55),('description',0.25),('location',0.20)]
    vals=[(similarity(a.get(k),b.get(k)),w) for k,w in fields]
    present=[(s,w) for s,w in vals if s is not None]
    if not present: return None
    return round(sum(s*w for s,w in present)/sum(w for _,w in present)*100,2)
