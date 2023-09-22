import os

def retrieve_sql(sql_command_directory_path):
    sql_files = [sqlfile for sqlfile in os.listdir(sql_command_directory_path) if sqlfile.endswith('.sql')]
    sorted_sql_files =  sorted(sql_files)
    return sorted_sql_files