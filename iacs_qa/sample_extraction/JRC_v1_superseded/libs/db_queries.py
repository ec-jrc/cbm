import pandas as pd
import numpy as np


def get_data_from_country(conn, country, columns, table_names): 

    parcels = table_names.get('parcels')
    
    query = f"""
        SELECT 
                {columns['intervention_id']} AS intervention_id, 
                {columns['holding_id']}::text AS holding_id, 
                {columns['parcel_id']} AS parcel_id, 
                {columns['covered']}::boolean AS covered, 
                {columns['ranking']} AS ranking
            FROM {parcels['schema']}.{parcels['name']} 
            WHERE {columns['country']} = '{country}'
            GROUP BY ranking, intervention_id, holding_id, parcel_id, covered
            ORDER by ranking, intervention_id, holding_id,  parcel_id, covered      
    """

    df = pd.read_sql_query(query,conn)
    df.set_index(['holding_id', 'parcel_id'], inplace = True)

    return df

def get_country_intervention_targets(conn, country, columns, table_names):

    targets = table_names.get('targets')

    query = f"""
        SELECT {columns['intervention_id']} as intervention_id, {columns['target']} AS target
        FROM {targets['schema']}.{targets['name']} 
        WHERE {columns['country']} = '{country}'
        """
        
    return pd.read_sql_query(query,conn)

def get_holding_id_per_intervention(conn, country, columns, table_names, min_holdings):

    parcels = table_names.get('parcels')

    query = f"""

        WITH 
        data AS(

            SELECT 
                {columns['intervention_id']} AS intervention_id, 
                {columns['holding_id']}::text AS holding_id,  
                {columns['ranking']} AS ranking,
                row_number() OVER (PARTITION by ua_grp_id ORDER BY ranking) AS row_number
            FROM {parcels['schema']}.{parcels['name']} 
            WHERE {columns['country']} = '{country}'
            ORDER by ranking, intervention_id, holding_id
        ),
        grouped AS(
            SELECT
                intervention_id,        
                min(ranking) as ranking,
                holding_id as holding_id,		
				min(row_number) as row_number
            FROM data
			WHERE row_number <= {min_holdings}
            GROUP BY intervention_id, holding_id
            ORDER by ranking, intervention_id   
        )    
        SELECT * FROM grouped  
    
    """
    
    return pd.read_sql_query(query,conn)


