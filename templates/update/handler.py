import json
import pymysql
import boto3

def update_template(event, context):
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
        # Extract the template ID, user ID, picture URL, is_public flag, and name from the event body
        body = json.loads(event['body'])
        template_id = event['pathParameters']['id']
        user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']
        is_public = body.get('is_public')
        name = body.get('name')

        # Check if the template exists and belongs to the user
        with conn.cursor() as cursor:
            sql = "SELECT user_id FROM templates WHERE id = %s"
            cursor.execute(sql, (template_id,))
            result = cursor.fetchone()

            if not result:
                # Template not found
                response = {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Template not found"})
                }
                return response

            if result['user_id'] != user_id:
                # Template does not belong to the user
                response = {
                    "statusCode": 403,
                    "body": json.dumps({"message": "Access denied"})
                }
                return response

        # Update the template in the templates table
        with conn.cursor() as cursor:
            sql = "UPDATE templates SET is_public = %s, name = %s WHERE id = %s"
            cursor.execute(sql, (is_public, name, template_id))
            conn.commit()

        # Prepare the response
        body = {
            "message": "Template updated successfully"
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
            "message": "Error updating template",
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
