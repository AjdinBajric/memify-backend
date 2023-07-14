import json
import pymysql
import boto3


def get_all_memes(event, context):
    # Fetch RDS connection details from Parameter Store
    parameter_store = boto3.client('ssm')
    rds_host = parameter_store.get_parameter(Name='memify-db-url')['Parameter']['Value']
    username = parameter_store.get_parameter(Name='memify-db-username')['Parameter']['Value']
    password = parameter_store.get_parameter(Name='memify-db-password', WithDecryption=True)['Parameter']['Value']
    db_name = parameter_store.get_parameter(Name='memify-db-name')['Parameter']['Value']

    # Get the pagination parameters from the event
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
        # Execute the SQL query without pagination
        with conn.cursor() as cursor:
            sql = '''
            SELECT
                m.id AS meme_id,
                p.image_url,
                m.date_created,
                m.name,
                COUNT(DISTINCT l.id) AS like_count,
                COUNT(DISTINCT s.id) AS share_count,
                COUNT(DISTINCT v.id) AS view_count
            FROM memes m
            JOIN pictures p ON m.picture_id = p.id
            LEFT JOIN likes l ON l.meme_id = m.id
            LEFT JOIN shares s ON s.meme_id = m.id
            LEFT JOIN views v ON v.meme_id = m.id
            GROUP BY m.id, p.image_url
            ORDER BY m.date_created DESC
            '''
            cursor.execute(sql)
            memes = cursor.fetchall()

        # Calculate the starting and ending indexes for the current page
        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        # Extract the memes for the current page
        memes_for_page = memes[start_index:end_index]

        # Prepare the response
        body = {
            "message": "Successfully retrieved memes",
            "memes": memes_for_page,
            "total": len(memes),
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(body, default=str)  # Serialize date objects as strings
        }

        return response

    except Exception as e:
        # Handle any exceptions that occur during the database operation
        # Prepare an error response
        error_message = str(e)
        body = {
            "message": "Error retrieving memes",
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
