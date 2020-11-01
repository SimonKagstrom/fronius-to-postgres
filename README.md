# fronius-to-postgres
Collect data from the Fronius Symo JSON API and store in a Postgres SQL database

Based on:
 - https://github.com/szymi-/fronius-to-influx
 - https://github.com/akleber/mqtt-connectors/blob/master/fronius-connector.py
 - Tutorials on https://www.postgresqltutorial.com/postgresql-python/

I don't know much about postgresql, so this is very much a hack. It probably
requires source code modifications to work for other people.


It's meant to be used with Grafana.
