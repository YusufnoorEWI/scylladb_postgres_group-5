from cassandra.cluster import Cluster
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table

from item import Item

session = Cluster(['127.0.0.1']).connect()
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS wdm
    WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
    """)

connection.setup(['127.0.0.1'], "wdm")


sync_table(Item)

item1 = Item.create(price=10, count=1)

print(item1)