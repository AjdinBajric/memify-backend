import json
import pymysql
import boto3

def create_share(event, context):
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
        # Extract the user ID and meme ID from the event
        user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']
        body = json.loads(event['body'])
        meme_id = body['meme_id']

        # Insert the new share into the table
        with conn.cursor() as cursor:
            sql = "INSERT INTO shares (user_id, meme_id, date_shared) VALUES (%s, %s, NOW())"
            cursor.execute(sql, (user_id, meme_id))
            conn.commit()

        # Prepare the response
        body = {
            "message": "New share added successfully"
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(body)
        }

        return response

    except Exception as e:
        # Handle any exceptions that occur during the database operation
        # Prepare an error response
        error_message = str(e)
        body = {
            "message": "Error adding new share",
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
