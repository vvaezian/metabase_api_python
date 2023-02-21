# This file does some initial setup so we can run tests on a local Metabase:
# - Downloads the Metabase jar file
# - Runs it
# - Creates an admin user (email: abc.xyz@gmail.com, password: xzy12345) and does the initial setup of Metabase
# - Creates some collections/cards/dashboards which will be used when running the tests

while getopts 'v:' flag; do
  case "${flag}" in
    v) MB_VERSION="${OPTARG}" ;;
    *) echo 'Accepted flags: -v'
       exit 1 ;;
  esac
done

if [[ $MB_VERSION = '' ]]
then
    echo 'Please provide the Metabase version using -v flag.'
    exit 1
fi

echo https://downloads.metabase.com/v$MB_VERSION/metabase.jar
pwd
ls -l
#cp tests/data/test_db.sqlite plugins

# wget https://downloads.metabase.com/v$MB_VERSION/metabase.jar
# echo "starting metabase jar locally ..."
# java -jar metabase.jar > logs 2>&1 &

# echo "waiting 60 seconds for the initialization to complete ..."
# sleep 60

# success='False'
# grep -q "Metabase Initialization COMPLETE" logs
# if [[ $? -eq 0 ]] 
# then 
#     echo 'success!'
#     success='True'
# else
#     echo "Waiting an extra 60 seconds for the initialization to complete"
#     sleep 60
#     grep -q "Metabase Initialization COMPLETE" logs
#     if [[ $? -eq 0 ]] 
#     then 
#         echo 'success!'
#         success='True'
#     else
#         echo 'failure!'
#     fi      
# fi

# if [[ $success = 'False' ]]
# then
#     exit 1
# fi

# echo "getting the seup token ..."
# setup_token=$(curl -X GET http://localhost:3000/api/session/properties | perl -pe 's/.*"setup-token":"(.*?)".*/\1/')
# echo "initial setup and getting session_id ..."
# session_id=$(curl -X POST -H "Content-Type: application/json" -d '{ "token": "'$setup_token'", "user": {"first_name": "abc", "last_name": "xyz", "email": "abc.xyz@gmail.com", "password": "xzy12345"},"prefs": {"allow_tracking": true, "site_name": "test_site"}}' http://localhost:3000/api/setup | perl -pe 's/^.......(.*)..$/\1/')
# echo $session_id

# echo "creaing base collections which will be used during the test ..."
# curl -X POST -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"name":"test_collection", "color":"#509EE3"}' http://localhost:3000/api/collection  # id of the created collection is 2 because id 1 is reserved for the personal collection of admin
# curl -X POST -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"name":"test_collection_dup", "parent_id":2, "color":"#509EE3"}' http://localhost:3000/api/collection  # collection_id: 3
# curl -X POST -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"name":"test_collection_dup", "parent_id":2, "color":"#509EE3"}' http://localhost:3000/api/collection  # collection_id: 4

# echo "downloading the test_db (SQLite)"  # for editing the SQLite db: https://sqliteviewer.flowsoft7.com/
# wget -P plugins/ https://github.com/vvaezian/metabase_api_python/raw/master/tests/data/test_db.sqlite

# echo "Connecting to test_db ..."
# curl -X POST -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"engine":"sqlite","name":"test_db","details":{"db":"plugins/test_db.sqlite","advanced-options":false},"is_full_sync":true}' http://localhost:3000/api/database  # id of the created db connection is 2 because 1 is used for sample database

# # echo "creating base cards which will be used during the test ..."
# json='{
#     "name": "test_card",
#     "display": "table",
#     "dataset_query": {
#         "database": 2,
#         "query": { "source-table": 9 },
#         "type": "query"
#     },
#     "visualization_settings": {},
#     "collection_id": 2
# }'
# echo "$json" | curl -X POST http://localhost:3000/api/card -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @- 

# json='{
#     "name":"test_card_2",
#     "dataset_query":{
#         "type":"native",
#         "native":{
#             "query":"select *\nfrom test_table\nwhere 1 = 1 \n[[ and {{test_filter}} ]]\n",
#             "template-tags":{
#                 "test_filter":{
#                     "name":"test_filter",
#                     "display-name":"Test filter",
#                     "type":"dimension",
#                     "dimension":["field",72,null],
#                     "widget-type":"string/=",
#                     "default":null,
#                     "id":"810912da-ead5-c87e-de32-6dc5723b9067"
#                 }
#             }
#         }
#         ,"database":2
#     },
#     "display":"table",
#     "visualization_settings":{},
#     "parameters":[{
#         "type":"string/=",
#         "target":["dimension",["template-tag","test_filter"]],
#         "name":"Test filter",
#         "slug":"test_filter",
#         "default":null,
#         "id":"810912da-ead5-c87e-de32-6dc5723b9067"
#     }],
#     "collection_id":2
# }'
# echo "$json" | curl -X POST http://localhost:3000/api/card -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @- 

# json='{
#     "name":"test_card_3",
#     "dataset_query":{
#         "type":"query",
#         "query":{
#             "source-table":9,
#             "filter":["=",["field",72,null],"row1 cell1","row3 cell1"]},
#             "database":2
#         },
#         "display":"table",
#         "visualization_settings":{},
#         "collection_id":2
# }'
# echo "$json" | curl -X POST http://localhost:3000/api/card -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @- 

# json='{
#     "name":"test_card_4",
#     "dataset":false,
#     "dataset_query":{
#         "database":2,
#         "query":{
#             "source-table":9,
#             "aggregation":[["avg",["field",73,null]]],
#             "breakout":[["field",72,null]],
#             "order-by":[["desc",["aggregation",0,null]]]
#             },
#         "type":"query"
#     },
#     "display":"bar",
#     "visualization_settings":{"table.pivot":false,"graph.dimensions":["col1"],"graph.metrics":["avg"]},
#     "collection_id":2
# }'
# echo "$json" | curl -X POST http://localhost:3000/api/card -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @- 

# # create a test dashboard
# curl -X POST http://localhost:3000/api/dashboard -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"collection_id":2,"name":"test_dashboard"}'

# # add the test_card to the dashboard
# curl -X POST http://localhost:3000/api/dashboard/1/cards -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d  '{"cardId":1}'
# json='{
#     "cards":[{
#             "card_id":1,
#             "row":0,
#             "col":0,
#             "size_x":4,
#             "size_y":5,
#             "series":[],
#             "visualization_settings":{},
#             "parameter_mappings":[]
#     }]
# }'
# echo "$json" | curl -X PUT http://localhost:3000/api/dashboard/1/cards -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @-

# # diable friendly table and field names
# curl -X PUT http://localhost:3000/api/setting/humanization-strategy -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"value":"none"}'

##session_id='69afe488-8037-47ec-b437-c6136d6d32c8'