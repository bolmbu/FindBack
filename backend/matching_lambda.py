"""DynamoDB Streams -> Matching Lambda -> Matches table -> SNS. Lab MVP."""
import hashlib
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from matching import score, THRESHOLD

REGION = os.getenv('AWS_REGION','us-east-1')
items = boto3.resource('dynamodb',region_name=REGION).Table(os.getenv('ITEMS_TABLE','LostAndFoundItems'))
matches = boto3.resource('dynamodb',region_name=REGION).Table(os.getenv('MATCHES_TABLE','LostAndFoundMatches'))
sns = boto3.client('sns',region_name=REGION)
TOPIC = os.getenv('SNS_TOPIC_ARN','')
DRY_RUN = os.getenv('DRY_RUN','true').lower()=='true'
decode = TypeDeserializer()

def scan_opposite(kind):
    kwargs={'FilterExpression':Attr('type').eq('FOUND' if kind=='LOST' else 'LOST')}
    while True:
        page=items.scan(**kwargs)
        yield from page.get('Items',[])
        if 'LastEvaluatedKey' not in page: break
        kwargs['ExclusiveStartKey']=page['LastEvaluatedKey']

def handler(event, context):
    output=[]
    for record in event.get('Records',[]):
        if record.get('eventName')!='INSERT': continue
        raw=record.get('dynamodb',{}).get('NewImage')
        if not raw: continue
        new={k:decode.deserialize(v) for k,v in raw.items()}
        if new.get('type') not in ('LOST','FOUND'): continue
        for old in scan_opposite(new['type']):
            if old.get('itemId')==new.get('itemId'): continue
            value=score(new,old)
            if value is None or value<THRESHOLD: continue
            mid=hashlib.sha256('|'.join(sorted([new['itemId'],old['itemId']])).encode()).hexdigest()
            status='DRY_RUN'
            if not DRY_RUN:
                if not TOPIC: raise ValueError('SNS_TOPIC_ARN not set')
                try:
                    matches.put_item(Item={
                        'matchId':mid, 'newItemId':new['itemId'], 'matchedItemId':old['itemId'],
                        'score':Decimal(str(value)), 'status':'PENDING',
                        'createdAt':datetime.now(timezone.utc).isoformat()},
                        ConditionExpression='attribute_not_exists(matchId)')
                except ClientError as ex:
                    if ex.response['Error']['Code']=='ConditionalCheckFailedException':
                        status='ALREADY_EXISTS'
                    else: raise
                else:
                    try:
                        sns.publish(TopicArn=TOPIC,Subject='FindBack - Possible Match',
                            Message=f"Possible match: {new.get('itemName')} <> {old.get('itemName')}\nScore: {value}%\nManual verification required.")
                    except Exception:
                        matches.update_item(Key={'matchId':mid},
                            UpdateExpression='SET #s = :v',
                            ExpressionAttributeNames={'#s':'status'},ExpressionAttributeValues={':v':'FAILED'})
                        raise
                    matches.update_item(Key={'matchId':mid},
                        UpdateExpression='SET #s = :v',
                        ExpressionAttributeNames={'#s':'status'},ExpressionAttributeValues={':v':'SENT'})
                    status='NOTIFIED'
            output.append({'matchId':mid,'score':value,'status':status})
    print(json.dumps({'matches':output}))
    return {'matchCount':len(output),'matches':output}
