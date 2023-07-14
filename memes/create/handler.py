import json
import pymysql
import boto3

def create_meme(event, context):
    # Retrieve the request body
    request_body = json.loads(event['body'])

    # Extract meme details from the request body
    picture_url = request_body.get('picture_url')
    user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']
    name = request_body.get('name')

    # Validate request parameters
    if not picture_url:
        response = {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request parameters'})
        }
        return response

    # Connect to the RDS database
    parameter_store = boto3.client('ssm')
    rds_host = parameter_store.get_parameter(Name='memify-db-url')['Parameter']['Value']
    username = parameter_store.get_parameter(Name='memify-db-username')['Parameter']['Value']
    password = parameter_store.get_parameter(Name='memify-db-password', WithDecryption=True)['Parameter']['Value']
    db_name = parameter_store.get_parameter(Name='memify-db-name')['Parameter']['Value']

    conn = pymysql.connect(
        host=rds_host,
        user=username,
        password=password,
        db=db_name,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cursor:
            # Insert the new picture into the pictures table
            sql = "INSERT INTO pictures (image_url, user_id, date_uploaded) VALUES (%s, %s, NOW())"
            cursor.execute(sql, (picture_url, user_id))
            picture_id = cursor.lastrowid

            # Insert the new meme into the memes table
            sql = "INSERT INTO memes (user_id, picture_id, name, date_created) VALUES (%s, %s, %s, NOW())"
            cursor.execute(sql, (user_id, picture_id, name))
            meme_id = cursor.lastrowid

        # Commit the transaction
        conn.commit()

        # Prepare the response
        response = {
            'statusCode': 200,
            'body': json.dumps({'message': 'Meme created successfully', 'meme_id': meme_id})
        }
        return response

    except Exception as e:
        # Handle any exceptions that occur during the database operation
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to create meme', 'message': str(e)})
        }
        return response

    finally:
        # Close the database connection
        conn.close()
