import json
import pymysql
import boto3

def create_template(event, context):
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
        # Extract the user ID, picture URL, is_public flag, and name from the event body
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']
        picture_url = body['picture_url']
        is_public = body['is_public']
        name = body['name']

        # Insert the new picture into the pictures table
        with conn.cursor() as cursor:
            sql = "INSERT INTO pictures (image_url, user_id, date_uploaded) VALUES (%s, %s, NOW())"
            cursor.execute(sql, (picture_url, user_id))
            conn.commit()
            picture_id = cursor.lastrowid

        # Insert the new template into the templates table
        with conn.cursor() as cursor:
            sql = "INSERT INTO templates (user_id, picture_id, is_public, name) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, picture_id, is_public, name))
            conn.commit()

        # Prepare the response
        body = {
            "message": "New template added successfully"
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
            "message": "Error adding new template",
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
