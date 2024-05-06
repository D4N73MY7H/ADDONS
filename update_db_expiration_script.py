import psycopg2
from psycopg2 import sql
from datetime import datetime


def get_all_databases(database_name, host, user_name, passwd, db_port):
    """Get all database names form the specified host
    :param database_name: the name of the initial odoo database used to connect with the host
    :param host: the name of the host
    :param user_name: username with admin privileges in host
    :param passwd: passwd of the specified user
    :param db_port: database port
    :return final_databases: list of databases in the specified instance, excluding postgres database and template databases
    """
    # Connection parameters for the PostgreSQL instance
    instance_params = {
        'host': host,
        'database': database_name,
        'user': user_name,
        'password': passwd,
        'port': db_port,
    }

    try:
        # Establish a connection to the PostgreSQL instance
        instance_connection = psycopg2.connect(**instance_params)
        instance_cursor = instance_connection.cursor()

        # Get the list of all databases
        instance_cursor.execute("SELECT datname FROM pg_database;")
        databases = instance_cursor.fetchall()
        # Initialize final databases variable
        final_databases = []

        if databases:
            for database in databases:
                if database[0] == 'postgres' or database[0].startswith('template'):
                    continue
                else:
                    final_databases.append(database[0])

        return final_databases

    except psycopg2.Error as e:
        print(f"Error connecting to the PostgreSQL instance: {e}")

    finally:
        # Close the PostgreSQL instance connection
        if instance_connection:
            instance_cursor.close()

            instance_connection.close()


def check_and_update_expiration_date(database_name, host, user_name, passwd, db_port, new_expiration_date):
    """Check and update expiration date of the databases in the host, if necessary
        :param database_name: the name of the initial odoo database used to connect with the host
        :param host: the name of the host
        :param user_name: username with admin privileges in host
        :param passwd: passwd of the specified user
        :param db_port: database port
        :return final_databases: list of databases in the specified instance, excluding postgres database and template databases
        """
    # Database connection parameters
    db_params = {
    'host': host,
    'database': database_name,
    'user': user_name,
    'password': passwd,
    'port': db_port,
    }

    # Query to check expiration date
    select_query = "SELECT * FROM ir_config_parameter WHERE key = 'database.expiration_date';"

    # Query to update expiration date
    update_query = "UPDATE ir_config_parameter SET value = %s WHERE key = 'database.expiration_date';"

    try:
        # Establish a database connection
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Execute the select query
        cursor.execute(select_query)
        result = cursor.fetchone()

        # Check if expiration date needs updating
        if result and result[1] != new_expiration_date:
            # Execute the update query
            cursor.execute(update_query, (new_expiration_date,))
            connection.commit()
            print(f"Expiration date updated successfully in database '{database_name}'.")
        else:
            print(f"No update needed or record not found in database '{database_name}'.")

    except psycopg2.Error as e:
        print(f"Error in database '{database_name}': {e}")
    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()


if __name__ == "__main__":
    # Host and database credentials
    database_name = 'postgres'
    host = 'localhost'
    user_name = 'postgres'
    passwd = 'postgres'
    db_port = '5432'

    # Desired expiration date
    new_expiration_date = '2100-02-11 17:01:10'

    # List of all databases in the specified instance
    databases = get_all_databases(database_name, host, user_name, passwd, db_port)

    try:
        if databases:
            for database in databases:
                # Execute the check_and_update_all_databases function
                check_and_update_expiration_date(database, host, user_name, passwd, db_port, new_expiration_date)
        else:
            print(f'There are no databases in the selected instance.')

    except Exception as e:
        print(f'An error occurred: {e}')

