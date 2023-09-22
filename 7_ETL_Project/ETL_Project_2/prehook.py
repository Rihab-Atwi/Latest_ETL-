import os
from database_handler import execute_query, create_connection, close_connection,return_data_as_df, return_create_statement_from_df
from lookups import ErrorHandling, PreHookSteps, SQLTablesToReplicate, InputTypes, SourceName, ETLStep, DestinationName
from logging_handler import show_error_message
from ETL_Project_2.misc_handler import retrieve_sql

# append the execute sql folder
# execute_sql_prehook
# execute_sql_hook
def execute_prehook_sql(db_session, sql_command_directory_path, target_schema):
    sql_files = retrieve_sql(sql_command_directory_path)
    for sql_file in sql_files:
        if str(sql_file.split('-')[0].split('_')[1]) == ETLStep.PRE_HOOK.value:
         with open(os.path.join(sql_command_directory_path,sql_file), 'r') as file:
            sql_query = file.read()
            sql_query = sql_query.replace('target_schema',target_schema.value)
            execute_query(db_session,sql_query)
    
def return_tables_by_schema(schema_name):
    schema_tables = list()
    tables = [table.value for table in SQLTablesToReplicate]
    for table in tables:
        if table.split('.')[0] == schema_name:
            schema_tables.append(table.split('.')[1])
    return schema_tables

def return_lookup_items_as_dict(lookup_item):
    enum_dict = {str(item.name).lower():item.value.replace(item.name.lower() + "_","") for item in lookup_item}
    return enum_dict
    

def create_sql_staging_table_index(db_session,source_name, table_name, index_val):
    query = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{index_val} ON {source_name}.{table_name} ({index_val});"
    execute_query(db_session,query)

def create_sql_staging_tables(db_session, source_name):
    try:
        source_name = source_name.value
        tables = return_tables_by_schema(source_name)
        for table in tables:
            staging_query = f"""
                    SELECT * FROM {source_name}.{table} LIMIT 1
            """
            staging_df = return_data_as_df(db_session= db_session, input_type= InputTypes.SQL, file_executor= staging_query)
            columns = list(staging_df.columns)
            dst_table = f"stg_{source_name}_{table}"
            create_stmt = return_create_statement_from_df(staging_df, 'dw_reporting', dst_table)
            execute_query(db_session=db_session, query= create_stmt)
            create_sql_staging_table_index(db_session, 'dw_reporting', dst_table, columns[0])
    except Exception as error:
        return staging_query


def execute_prehook(sql_command_directory_path = './SQL_Commands'):
    step_name = ""
    try:
        db_session = create_connection()
        execute_prehook_sql(db_session, sql_command_directory_path, DestinationName.Datawarehouse) 
        create_sql_staging_tables(db_session,SourceName.DVD_RENTAL)
        close_connection(db_session)
    except Exception as error:
        suffix = str(error)
        error_prefix = ErrorHandling.PREHOOK_SQL_ERROR
        show_error_message(error_prefix.value, suffix)
        raise Exception(f"Important Step Failed step = {step_name}")