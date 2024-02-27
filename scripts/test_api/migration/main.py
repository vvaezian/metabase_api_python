"""
On a besoin:
* du (source) collection_id
* du db_target
* Mapping table_src -> table_target, pour toutes les tables referencees a la source (dans les cartes)
"""

from metabase_api.metabase_api import Metabase_API
from metabase_api.migration import migrate_collection

# test
source_collection_id = 266
db_target = 3
table_src2dst = {
    61: 61,
}
PARENT_COLLECTION_ID = 69
destination_collection_name = f"test2_test"
#

# # CHUM from MUHC --------------------
# source_collection_id = 64
# db_target = 3
# table_src2dst = {
#     77: 77,
# }
# PARENT_COLLECTION_ID = 244
# destination_collection_name=f"chum"
# # END CHUM from MUHC --------------------

print(f"destination_collection_name = '{destination_collection_name}'")


migrate_collection(
    metabase_api=Metabase_API(
        "https://assistiq.metabaseapp.com", "wafa@assistiq.ai", "AssistIQ2023."
    ),
    source_collection_id=source_collection_id,
    db_target=db_target,
    PARENT_COLLECTION_ID=PARENT_COLLECTION_ID,
    destination_collection_name=destination_collection_name,
    table_src2dst=table_src2dst,
)
