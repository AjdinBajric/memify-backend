import json
import pymysql
import boto3

def get_meme_by_id(event, context):
    # Fetch RDS connection details from Parameter Store
    parameter_store = boto3.client('ssm')
    rds_host = parameter_store.get_parameter(Name='memify-db-url')['Parameter']['Value']
    username = parameter_store.get_parameter(Name='memify-db-username')['Parameter']['Value']
    password = parameter_store.get_parameter(Name='memify-db-password', WithDecryption=True)['Parameter']['Value']
    db_name = parameter_store.get_parameter(Name='memify-db-name')['Parameter']['Value']

    # Extract meme ID from path parameters
    meme_id = event['pathParameters']['id']

    # Connect to the RDS database
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

            # Return picture URL, title, views, likes and shares for the meme.
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
            WHERE m.id = %s
            GROUP BY m.id, p.image_url
            '''
            cursor.execute(sql, (meme_id,))
            result = cursor.fetchone()

            if result:
                body = {
                    "message": "Meme retrieved successfully",
                    "meme": result
                }
                status_code = 200
            else:
                body = {
                    "message": "Meme not found"
                }
                status_code = 404

        response = {
            "statusCode": status_code,
            "body": json.dumps(body, default=str)
        }

        return response

    finally:
        # Close the database connection
        conn.close()