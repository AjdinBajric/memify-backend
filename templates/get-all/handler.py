import json
import pymysql
import boto3


def get_all_templates(event, context):
    # Fetch RDS connection details from Parameter Store
    parameter_store = boto3.client('ssm')
    rds_host = parameter_store.get_parameter(Name='memify-db-url')['Parameter']['Value']
    username = parameter_store.get_parameter(Name='memify-db-username')['Parameter']['Value']
    password = parameter_store.get_parameter(Name='memify-db-password', WithDecryption=True)['Parameter']['Value']
    db_name = parameter_store.get_parameter(Name='memify-db-name')['Parameter']['Value']

    # Get the pagination parameters from the query string
    page = int(event['queryStringParameters'].get('page', 1))
    per_page = int(event['queryStringParameters'].get('per_page', 10))

    # Connect to the RDS instance
    conn = pymysql.connect(
        host=rds_host,
        user=username,
        password=password,
        db=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        # Retrieve templates without pagination
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
                        WHERE t.is_public = 1
                        ORDER BY t.id DESC;
                   '''
            cursor.execute(sql)
            templates = cursor.fetchall()

        # Calculate the starting and ending indexes for the current page
        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        # Extract the templates for the current page
        templates_for_page = templates[start_index:end_index]

        # Prepare the response
        body = {
            "templates": templates_for_page,
            "total": len(templates),
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(body, default=str),
        }

        return response

    except Exception as e:
        # Handle any exceptions that occur during the database operation
        # Prepare an error response
        error_message = str(e)
        body = {
            "message": "Error retrieving templates",
            "error": error_message,
        }

        response = {
            "statusCode": 500,
            "body": json.dumps(body),
        }

        return response

    finally:
        # Close the database connection
        conn.close()
