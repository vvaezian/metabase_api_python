[![GitHub license](https://img.shields.io/github/license/vvaezian/metabase_api_python.svg)](https://github.com/vvaezian/metabase_api_python/blob/master/LICENSE)

## Previous Work
This is an AssistIQ-maintained clone of the original package;
see [the original README](./README_ORIG.md) for further details.

## Installation
`git clone` this repo

## Invocation

### Setup
For authentification, 2 environment variables need to be set:
* `METABASE_LOGIN`, with a proper metabase user login
* `METABASE_PASSWD`, with the corresponding password

You want this account to have admin-like permissions.

### Call
Main script is

`python scripts/test_api/migration/main.py`

#### Parameters
* `--from` name of the dashboard to migrate
* `--db_target`: name of the target DB, as identified in metabase's sources (eg, `dev-chum`)
* `--to_parent`: _id_ (**not** _name_) of parent collection where to migrate
* `--to`: collection of resulting migrated dashboard
* `--name`: name of resulting migrated dashboard
* `--personalization`: (Optional) json file with personalization options

#### Personalization options
A json structure with 2 fields: `language` and `fields_replacements`.
Let's see an example:
```commandline
{
  "language": "FR",
  "fields_replacements": {
    "l_name": "_dr_id",
    "name_en": "name_fr",
    "procedure_en": "procedure_fr"
  }
}
```
* `language` is a two-letter identification for target language. Above, it is set to French.
* `fields_replacements` consistents of a list of pairs `column_src`: `column_target`

## Contact
AssistIQ team, specifically Luis Da Costa.
