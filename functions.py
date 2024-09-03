import mysql.connector
from mysql.connector import Error
from flask import session



def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host = 'erixconsulting.mysql.pythonanywhere-services.com',
            user = 'erixconsulting',
            password = '5498603Ma.',
            database = 'erixconsulting$default'


            )

        return connection
    except Error as e:
        print(f"The error '{e}' occured")
        return None