import boto3
import pymysql

def hello(event, context):
    # Retrieve the Cognito user ID (sub attribute) from the event
    user_id = event['request']['userAttributes']['sub']

    parameter_store = boto3.client('ssm')
    rds_host = parameter_store.get_parameter(Name='memify-db-url')['Parameter']['Value']
    username = parameter_store.get_parameter(Name='memify-db-username')['Parameter']['Value']
    password = parameter_store.get_parameter(Name='memify-db-password', WithDecryption=True)['Parameter']['Value']
    db_name = parameter_store.get_parameter(Name='memify-db-name')['Parameter']['Value']

    # Connect to your RDS database
    connection = pymysql.connect(
        host=rds_host,
        user=username,
        password=password,
        database=db_name,
    )

    try:
        with connection.cursor() as cursor:
            # Insert the user into the RDS table
            sql = "INSERT INTO users (id, username, password, email) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, 'username', 'password', 'email'))
        connection.commit()
    finally:
        connection.close()

    return event
