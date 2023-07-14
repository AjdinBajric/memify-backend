import json
import pymysql
import boto3
from datetime import date

def serialize_date(obj):
    if isinstance(obj, date):
        return obj.isoformat()

def get_all_likes_by_meme_id(event, context):
    # Fetch RDS connection details from Parameter Store
    parameter_store = boto3.client('ssm')
    rds_host = parameter_store.get_parameter(Name='memify-db-url')['Parameter']['Value']
    username = parameter_store.get_parameter(Name='memify-db-username')['Parameter']['Value']
    password = parameter_store.get_parameter(Name='memify-db-password', WithDecryption=True)['Parameter']['Value']
    db_name = parameter_store.get_parameter(Name='memify-db-name')['Parameter']['Value']

    # Connect to the RDS instance
    conn = pymysql.connect(
        host=rds_host,
        user=username,
        password=password,
        db=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        # Extract the meme ID from the event
        meme_id = event['pathParameters']['meme_id']

        # Retrieve all likes for the meme ID
        with conn.cursor() as cursor:
            sql = "SELECT * FROM likes WHERE meme_id = %s"
            cursor.execute(sql, (meme_id,))
            likes = cursor.fetchall()

        # Serialize the date objects
        for like in likes:
            like['date_liked'] = serialize_date(like['date_liked'])

        # Prepare the response
        body = {
            "likes": likes
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(body, default=serialize_date)
        }

        return response

    except Exception as e:
        # Handle any exceptions that occur during the database operation
        # Prepare an error response
        error_message = str(e)
        body = {
            "message": "Error retrieving likes",
            "error": error_message
        }

        response = {
            "statusCode": 500,
            "body": json.dumps(body)
        }

        return response

    finally:
        # Close the database connection
        conn.close()
