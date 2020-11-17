str = """title = "Gn2Gn Client Config sample"

[db]
db_host = "localhost"
db_port = 5432
db_user = "<dbUser>"
db_password = "<dbPassword>"
db_name = "<dbName>"
db_schema_import = "schema"
    [db.db_querystring]
    sslmode = "prefer"

[[source]]
name = "Source1"
user_name = "<monuser>"
user_password = "<monPwd>"
export_module_api_url = "<http://geonature/API/EXPORT>"
export_id = 1

[[source]]
name = "Source2"
user_name = "<monuser>"
user_password = "<monPwd>"
export_module_api_url = "<http://geonature/API/EXPORT>"
export_id = 1
"""

import toml
from pprint import pprint

data = toml.loads(str)

pprint(data["db"])
