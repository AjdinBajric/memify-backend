import json
import pymysql
import boto3

def get_my_templates(event, context):
    # Fetch RDS connection details from Parameter Store
    parameter_store = boto3.client('ssm')
    rds_host = parameter_store.get_parameter(Name='memify-db-url')['Parameter']['Value']
    username = parameter_store.get_parameter(Name='memify-db-username')['Parameter']['Value']
    password = parameter_store.get_parameter(Name='memify-db-password', WithDecryption=True)['Parameter']['Value']
    db_name = parameter_store.get_parameter(Name='memify-db-name')['Parameter']['Value']

    # Extract the user ID from the event
    user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']

    # Connect to the RDS instance
    conn = pymysql.connect(
        host=rds_host,
        user=username,
        password=password,
        db=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        # Retrieve templates by user ID from the table
        with conn.cursor() as cursor:
            sql = '''SELECT
                      t.id AS template_id,
                      p.image_url,
                      t.name,
                      t.is_public,
                      p.date_uploaded,
                      (SELECT COUNT(*) FROM memes m WHERE m.picture_id = t.picture_id) AS num_of_times_used
                    FROM templates t
                    JOIN pictures p ON t.picture_id = p.id
                    WHERE t.user_id = %s;
                  '''
            cursor.execute(sql, (user_id,))
            templates = cursor.fetchall()

        # Prepare the response
        body = {
            "templates": templates
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(body, default=str)
        }

        return response

    except Exception as e:
        # Handle any exceptions that occur during the database operation
        # Prepare an error response
        error_message = str(e)
        body = {
            "message": "Error retrieving templates by user ID",
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
