"""Check all available LinkedIn analytics fields."""
import sys, json

data = json.load(sys.stdin)
if 'elements' not in data:
    print('ERROR:', json.dumps(data)[:500])
    sys.exit(1)
el = data['elements'][0]
keys = sorted(el.keys())
print(f'TOTAL FIELDS: {len(keys)}')
print()
print('--- NON-ZERO ---')
for k in keys:
    v = el[k]
    if v is not None and v != 0:
        print(f'  {k}: {str(v)[:100]}')
print()
print('--- ZERO ---')
for k in keys:
    if el[k] == 0:
        print(f'  {k}')
