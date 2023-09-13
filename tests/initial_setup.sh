# This file does some initial setup so we can run tests on a local Metabase:
# - Downloads the Metabase jar file
# - Runs it and waits for initialization to complete
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

# cleaup (in case the script is not running for the first time)
rm -f metabase.db.mv.db
rm -f metabase.db.trace.db

# downloading metabase jar file
wget -O metabase.jar -q https://downloads.metabase.com/v$MB_VERSION/metabase.jar

# starting metabase jar locally
java -jar metabase.jar > logs 2>&1 &

# waiting 45 seconds for the initialization to complete
sleep 45

# checking whether the metabase initialization has completed. If not, wait another 45 seconds
success='False'
grep -q "Metabase Initialization COMPLETE" logs
if [[ $? -eq 0 ]] 
then 
    echo 'success!'
    success='True'
else
    echo "Waiting an extra 45 seconds for the initialization to complete"
    sleep 45
    grep -q "Metabase Initialization COMPLETE" logs
    if [[ $? -eq 0 ]] 
    then 
        echo 'success!'
        success='True'
    else
        echo 'failure!'
    fi      
fi

if [[ $success = 'False' ]]
then
    exit 1
fi


# getting the seup token
setup_token=$(curl -X GET http://localhost:3000/api/session/properties | perl -pe 's/.*"setup-token":"(.*?)".*/\1/')
# initial setup and getting the session_id
session_id=$(curl -X POST -H "Content-Type: application/json" -d '{ "token": "'$setup_token'", "user": {"first_name": "abc", "last_name": "xyz", "email": "abc.xyz@gmail.com", "password": "xzy12345"},"prefs": {"allow_tracking": true, "site_name": "test_site"}}' http://localhost:3000/api/setup | perl -pe 's/^.......(.*)..$/\1/')
echo $session_id

# copying the SQLite test db to metabase plugins directory (for editing the SQLite db you can use: https://sqliteviewer.flowsoft7.com/)
cp tests/data/test_db.sqlite plugins
# adding test_db to Metabase as a new database
curl -X POST -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"engine":"sqlite","name":"test_db","details":{"db":"plugins/test_db.sqlite","advanced-options":false},"is_full_sync":true}' http://localhost:3000/api/database  # id of the created db connection is 2 because 1 is used for sample database

# creaing base collections which will be used during the test
curl -X POST -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"name":"test_collection", "color":"#509EE3"}' http://localhost:3000/api/collection  # id of the created collection is 2 because id 1 is reserved for the personal collection of admin
curl -X POST -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"name":"test_collection_dup", "parent_id":2, "color":"#509EE3"}' http://localhost:3000/api/collection  # collection_id: 3
curl -X POST -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"name":"test_collection_dup", "parent_id":2, "color":"#509EE3"}' http://localhost:3000/api/collection  # collection_id: 4

# creating base cards which will be used during the test
json='{
    "name": "test_card",
    "display": "table",
    "dataset_query": {
        "database": 2,
        "query": { "source-table": 9 },
        "type": "query"
    },
    "visualization_settings": {},
    "collection_id": 2
}'
echo "$json" | curl -X POST http://localhost:3000/api/card -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @- > output

# the order of the IDs assigned to columns is not based on the db column order
grep -q ',73.*,72' output
if [[ $? -eq 0 ]]; then 
    col1_id=73;
    col2_id=72; 
else 
    col1_id=72;
    col2_id=73; 
fi

json='{
    "name":"test_card_2",
    "dataset_query":{
        "type":"native",
        "native":{
            "query":"select *\nfrom test_table\nwhere 1 = 1 \n[[ and {{test_filter}} ]]\n",
            "template-tags":{
                "test_filter":{
                    "name":"test_filter",
                    "display-name":"Test filter",
                    "type":"dimension",
                    "dimension":["field",COL1_ID,null],
                    "widget-type":"string/=",
                    "default":null,
                    "id":"810912da-ead5-c87e-de32-6dc5723b9067"
                }
            }
        }
        ,"database":2
    },
    "display":"table",
    "visualization_settings":{},
    "parameters":[{
        "type":"string/=",
        "target":["dimension",["template-tag","test_filter"]],
        "name":"Test filter",
        "slug":"test_filter",
        "default":null,
        "id":"810912da-ead5-c87e-de32-6dc5723b9067"
    }],
    "collection_id":2
}'
# add the value of $col1_id (because of presense of single and double quotes in the json string, I decided to add the variable value in this way)
json=$(echo "$json" | sed "s/COL1_ID/$col1_id/g")

echo "$json" | curl -X POST http://localhost:3000/api/card -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @- 

json='{
    "name":"test_card_3",
    "dataset_query":{
        "type":"query",
        "query":{
            "source-table":9,
            "filter":["=",["field",COL1_ID,null],"row1 cell1","row3 cell1"]},
            "database":2
        },
        "display":"table",
        "visualization_settings":{},
        "collection_id":2
}'
# add the value of $col1_id 
json=$(echo "$json" | sed "s/COL1_ID/$col1_id/g")

echo "$json" | curl -X POST http://localhost:3000/api/card -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @- 

json='{
    "name":"test_card_4",
    "dataset":false,
    "dataset_query":{
        "database":2,
        "query":{
            "source-table":9,
            "aggregation":[["avg",["field",COL2_ID,null]]],
            "breakout":[["field",COL1_ID,null]],
            "order-by":[["desc",["aggregation",0,null]]]
            },
        "type":"query"
    },
    "display":"bar",
    "visualization_settings":{"table.pivot":false,"graph.dimensions":["col1"],"graph.metrics":["avg"]},
    "collection_id":2
}'
# add the value of $col1_id and $col2_id
json=$(echo "$json" | sed "s/COL1_ID/$col1_id/g" | sed "s/COL2_ID/$col2_id/g")

echo "$json" | curl -X POST http://localhost:3000/api/card -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @- 

# create a test dashboard
curl -X POST http://localhost:3000/api/dashboard -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"collection_id":2,"name":"test_dashboard"}'
# add the test_card to the dashboard
curl -X POST http://localhost:3000/api/dashboard/1/cards -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d  '{"cardId":1}'
json='{
    "cards":[{
            "card_id":1,
            "row":0,
            "col":0,
            "size_x":4,
            "size_y":5,
            "series":[],
            "visualization_settings":{},
            "parameter_mappings":[]
    }]
}'
echo "$json" | curl -X PUT http://localhost:3000/api/dashboard/1/cards -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d @-

# diable friendly table and field names
curl -X PUT http://localhost:3000/api/setting/humanization-strategy -H "Content-Type: application/json" -H "X-Metabase-Session:$session_id" -d '{"value":"none"}'
