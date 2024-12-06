[![GitHub license](https://img.shields.io/github/license/vvaezian/metabase_api_python.svg)](https://github.com/vvaezian/metabase_api_python/blob/master/LICENSE)

## Previous Work
This is an AssistIQ-maintained clone of the original package;
see [the original README](./README_ORIG.md) for further details.

--------

Developer's guide
------------

## Installation
`git clone` this repo

## Python environment
We use [conda](https://docs.conda.io/en/latest/miniconda.html) to manage our environments.
To install the `metabase_api` environment do
```
conda env create
```
or, to update your existing environment:
```
conda env update -f environment.yml
```
and then
```commandline
conda env update -f environment-dev.yml
```
Then `conda activate metabase_api`


--------

Invocation
------------

### Setup
For authentification, 2 environment variables need to be set:
* `METABASE_LOGIN`, with a proper metabase user login
* `METABASE_PASSWD`, with the corresponding password

You want this account to have admin-like permissions.

### Executables
There are 2 available functionalities in this repo: **migration** and **labels generation**

#### Label generation (for specific language)
This utility serves to generate all labels needed in a specific language.
Main script is

`python scripts/test_api/migration/generate_language_config.py`

##### Parameters
* `--from` name of the dashboard where to pull labels from
* `--language`: language to translate to (eg, `FR`)
* `--to`: filename where to write the results

There are previously-generated translation files in directory `resources`
(called something like `labels_en2fr.json`, for EN to FR translation)

#### Migration
Main script is

`python scripts/test_api/migration/main.py`



--numbers
/Users/luis/dev/metabase_api_python/metabase_api/resources/hospitals_config/numbers_fr.json

##### Parameters
* `--from` name of the dashboard to migrate
* `--db_target`: name of the target DB, as identified in metabase's sources (eg, `dev-chum`)
* `--to_parent`: _id_ (**not** _name_) of parent collection where to migrate
* `--to`: collection of resulting migrated dashboard
* `--name`: name of resulting migrated dashboard
* `--fields`: (Optional) json file with fields' replacements
* `--labels`: (Optional) json file with labels' replacements
* `--numbers`: json file with number personalization options

##### Fields

A json structure specifying which field to replace with
which other one. It consists of a list of pairs `column_src`: `column_target`

Let's see an example:
```commandline
{
    "l_name": "_dr_id",
    "name_en": "name_fr",
    "procedure_en": "procedure_fr"
}
```

##### Labels

Like `fields` above, a json structure specifying
which label to replace with
which other one.
It consists of a list of pairs `label_src`: `label_target`

Example:
```commandline
{
    Active Physicians": "Médecins actifs",
    "All Categories": "Toutes les catégories"
}
```
#### Numbers

Specification of how we want the numbers to be formatted.
You can see an example on `metabase_api/resources/hospitals_config/numbers_en.json`

Example:
```commandline
{
  "numbers": {
    "number_style": "decimal",
    "number_separators": ", ",
    "currency": {
      "suffix": "",
      "prefix": "$"
    },
    "other": {
      "suffix": "",
      "prefix": ""
    }
  }
}
```



## Contact
AssistIQ team, specifically Luis Da Costa.
