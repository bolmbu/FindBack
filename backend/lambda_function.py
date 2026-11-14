"""FindBack lab API. Python 3.13, boto3 bundled with Lambda runtime."""
import base64
import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import unquote
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

REGION = os.getenv('AWS_REGION', 'us-east-1')
ITEMS_TABLE = os.getenv('ITEMS_TABLE', 'LostAndFoundItems')
MATCHES_TABLE = os.getenv('MATCHES_TABLE', 'LostAndFoundMatches')
BUCKET = os.getenv('IMAGE_BUCKET', '')
ENABLE_UPLOAD = os.getenv('ENABLE_DEMO_UPLOAD', 'false').lower() == 'true'
db = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
items = db.Table(ITEMS_TABLE)
matches = db.Table(MATCHES_TABLE)


def encode(o):
    if isinstance(o, Decimal):
        return float(o)
    raise TypeError(f'Unserializable: {type(o)}')


def respond(status, data):
    return {'statusCode': status, 'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(data, default=encode, ensure_ascii=False)}


def signed_image(item):
    image_key = item.get('imageKey')
    if not image_key or not BUCKET:
        return None
    try:
        return s3.generate_presigned_url('get_object', Params={'Bucket': BUCKET, 'Key': image_key}, ExpiresIn=300)
    except ClientError:
        return None


def body_from(event):
    raw = event.get('body') or '{}'
    if event.get('isBase64Encoded'):
        raw = base64.b64decode(raw)
    return json.loads(raw)


def page_scan(table, limit=100):
    output, kwargs = [], {}
    while len(output) < limit:
        res = table.scan(**kwargs)
        output.extend(res.get('Items', []))
        if 'LastEvaluatedKey' not in res:
            break
        kwargs['ExclusiveStartKey'] = res['LastEvaluatedKey']
    return output[:limit]


def list_items():
    found = page_scan(items, 100)
    found.sort(key=lambda i: i.get('createdAt', ''), reverse=True)
    for i in found:
        i['imageUrl'] = signed_image(i)
    return respond(200, {'items': found, 'count': len(found)})


def list_matches():
    output = []
    for m in page_scan(matches, 100):
        a_id, b_id = m.get('newItemId'), m.get('matchedItemId')
        if not a_id or not b_id:
            continue
        a = items.get_item(Key={'itemId': a_id}).get('Item')
        b = items.get_item(Key={'itemId': b_id}).get('Item')
        if not a or not b or {a.get('type'), b.get('type')} != {'LOST', 'FOUND'}:
            continue
        lost, found = (a, b) if a['type'] == 'LOST' else (b, a)
        for it in (lost, found):
            it['imageUrl'] = signed_image(it)
        output.append({'matchId': m['matchId'], 'score': float(m.get('score', 0)),
                       'notificationStatus': m.get('status', 'UNKNOWN'),
                       'reviewStatus': 'PENDING_REVIEW',
                       'lostItem': lost, 'foundItem': found})
    output.sort(key=lambda m: m['score'], reverse=True)
    return respond(200, {'matches': output, 'count': len(output)})


def create_item(event):
    try:
        p = body_from(event)
    except (ValueError, TypeError):
        return respond(400, {'message': 'Invalid JSON body'})
    name = p.get('itemName')
    kind = str(p.get('type', '')).upper()
    if not isinstance(name, str) or not name.strip() or kind not in {'LOST', 'FOUND'}:
        return respond(400, {'message': 'Valid itemName and LOST/FOUND type required'})
    image_key = p.get('imageKey')
    if image_key:
        if not BUCKET or not isinstance(image_key, str) or not image_key.startswith('uploads/'):
            return respond(400, {'message': 'Invalid imageKey'})
        try:
            meta = s3.head_object(Bucket=BUCKET, Key=image_key)
            if meta['ContentLength'] > 2 * 1024 * 1024 or meta.get('ContentType') not in ('image/jpeg','image/png','image/webp'):
                return respond(400, {'message': 'Unsupported image'})
        except ClientError:
            return respond(400, {'message': 'Uploaded image not found'})
    it = {'itemId': str(uuid.uuid4()), 'itemName': name.strip()[:160], 'type': kind,
          'location': str(p.get('location') or '')[:180],
          'description': str(p.get('description') or '')[:1000],
          'status': 'OPEN', 'createdAt': datetime.now(timezone.utc).isoformat()}
    if image_key: it['imageKey'] = image_key
    items.put_item(Item=it)
    it['imageUrl'] = signed_image(it)
    return respond(201, {'message': 'Item created', 'item': it})


def upload_url(event):
    if not ENABLE_UPLOAD:
        return respond(403, {'message': 'Image upload is disabled'})
    if not BUCKET:
        return respond(500, {'message': 'IMAGE_BUCKET is not configured'})
    try: p = body_from(event)
    except (ValueError, TypeError): return respond(400, {'message':'Invalid JSON'})
    ct = p.get('contentType') or p.get('content_type')
    allowed = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
    if ct not in allowed:
        return respond(400, {'message': 'Unsupported file type'})
    key = f"uploads/{uuid.uuid4()}{allowed[ct]}"
    # Multipart overhead allowance; the browser also enforces 2MB file maximum.
    presigned = s3.generate_presigned_post(
        Bucket=BUCKET, Key=key,
        Fields={'Content-Type': ct},
        Conditions=[{'Content-Type': ct}, ['content-length-range', 1, 2*1024*1024+8192]],
        ExpiresIn=60)
    return respond(200, {'uploadUrl': presigned['url'], 'url': presigned['url'],
                         'fields': presigned['fields'], 'imageKey': key,
                         'key': key, 'upload': presigned})


def lambda_handler(event, context):
    method = (event.get('requestContext', {}).get('http', {}).get('method')
              or event.get('httpMethod') or 'GET').upper()
    path = (event.get('rawPath') or event.get('path') or '/').rstrip('/')
    if method == 'GET' and path == '/items': return list_items()
    if method == 'GET' and path == '/matches': return list_matches()
    if method == 'POST' and path == '/items': return create_item(event)
    if method == 'POST' and path == '/upload-url': return upload_url(event)
    return respond(404, {'message':'Route not found'})
