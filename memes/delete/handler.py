import json
import pymysql
import boto3

def delete_meme(event, context):
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
        # Extract meme ID from the event
        meme_id = event['pathParameters']['id']
        user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']

        # Delete the meme from the database
        with conn.cursor() as cursor:
            sql = "DELETE FROM memes WHERE user_id = %s AND id = %s"
            cursor.execute(sql, (user_id, meme_id))
            conn.commit()

        # Prepare the response
        body = {
            "message": "Meme deleted successfully"
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
            "message": "Error deleting meme",
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
