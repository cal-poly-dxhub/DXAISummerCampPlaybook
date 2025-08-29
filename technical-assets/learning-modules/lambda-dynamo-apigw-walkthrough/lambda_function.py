import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table_name = 'demo-camp-table'
table = dynamodb.Table(table_name)

def write_item_to_dynamo(item):
    response = table.put_item(Item=item)
    print("Write successful:", response)
    return response

def lambda_handler(event, context):
    body = event
    if 'id' not in body:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required field: id'})
        }

    response = write_item_to_dynamo(body)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Item written successfully'})
    }
