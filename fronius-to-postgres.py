#!/usr/bin/env python

# Based on:
# - https://github.com/szymi-/fronius-to-influx
# - https://github.com/akleber/mqtt-connectors/blob/master/fronius-connector.py
# - Tutorials on https://www.postgresqltutorial.com/postgresql-python/

# I don't really know how this works, so it's a big hack...

import requests
import time
import logging
import sys
import psycopg2
import json
from datetime import datetime

input = '''
{
   "Body" : {
      "Data" : {
         "Inverters" : {
            "1" : {
               "DT" : 111,
               "E_Day" : 516.10003662109375,
               "E_Total" : 3718140,
               "E_Year" : 3718148,
               "P" : 5
            }
         },
         "Site" : {
            "E_Day" : 516.10003662109375,
            "E_Total" : 3718140,
            "E_Year" : 3718148,
            "Meter_Location" : "unknown",
            "Mode" : "produce-only",
            "P_Akku" : null,
            "P_Grid" : null,
            "P_Load" : null,
            "P_PV" : 19,
            "rel_Autonomy" : null,
            "rel_SelfConsumption" : null
         },
         "Version" : "12"
      }
   },
   "Head" : {
      "RequestArguments" : {},
      "Status" : {
         "Code" : 0,
         "Reason" : "",
         "UserMessage" : ""
      },
      "Timestamp" : "2020-11-01T14:01:41+01:00"
   }
}'''

create_command = '''
CREATE TABLE IF NOT EXISTS braxen_fronius (
                time TIMESTAMP NOT NULL,
                e_pv INTEGER NOT NULL,
                e_day FLOAT(8) NOT NULL,
                e_year FLOAT(8) NOT NULL,
                e_total FLOAT(8) NOT NULL
)
'''

def fronius_data(fronius_ip):

    values = {}

    try:
        url = "http://{}/solar_api/v1/GetPowerFlowRealtimeData.fcgi".format(fronius_ip)  # noqa E501
        r = requests.get(url, timeout=3 - 0.5)
        r.raise_for_status()
        powerflow_data = r.json()

        values['p_pv'] = powerflow_data['Body']['Data']['Site']['P_PV']
        values['e_day'] = powerflow_data['Body']['Data']['Site']['E_Day'] / 1000
        values['e_year'] = powerflow_data['Body']['Data']['Site']['E_Year'] / 1000
        values['e_total'] = powerflow_data['Body']['Data']['Site']['E_Total'] / 1000

        # handling for null/None values
        for k, v in values.items():
            if v is None:
                values[k] = 0

    except requests.exceptions.Timeout:
        print("Timeout requesting {}".format(url))
    except requests.exceptions.RequestException as e:
        print("requests exception {}".format(e))

    return values

def connect(postgres_host, postgres_database, postgres_user, postgres_password):
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(host=postgres_host,
            database=postgres_database,
            user=postgres_user,
            password=postgres_password)

        return conn

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None

def create_table(conn):
    try:
        # create a cursor
        cur = conn.cursor()

        cur.execute(create_command)
        cur.close()
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

def insert_entry(conn, values):
    try:
        # create a cursor
        cur = conn.cursor()

        sql = '''INSERT INTO braxen_fronius (time, e_pv, e_day, e_year, e_total)
        VALUES(%s,%s,%s,%s,%s);'''
        sql_values = (datetime.now(),
            values['p_pv'],
            values['e_day'],
            values['e_year'],
            values['e_total']
        )
        cur.execute(sql, sql_values)
        cur.close()
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print("Usage: XXX <fronius-IP> <postgres-host> <postgres-database> <postgres-user> <postgres-password>")
        sys.exit(1)
    fronius_ip = sys.argv[1]
    postgres_host = sys.argv[2]
    postgres_database = sys.argv[3]
    postgres_user = sys.argv[4]
    postgres_password = sys.argv[5]

    conn = connect(postgres_host, postgres_database, postgres_user, postgres_password)

    create_table(conn)

    last_values = {
        'p_pv' : 1000000,
        'e_day' : 0,
        'e_year' : 0,
        'e_total' : 0,
    }

    while True:
        values = fronius_data(fronius_ip)
        if values != {}:
            if values['p_pv'] == last_values['p_pv'] and values['e_day'] == last_values['e_day']:
                print("Unchanged values, skipping")
                time.sleep(120)
                continue

            print("Inserting new entry", values)

            last_values = values
            insert_entry(conn, values)
        else:
            print("No reply from fronius, skipping")

        time.sleep(300)

    sys.exit(0)
