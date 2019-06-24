#!/bin/bash
# Copyright (C) <2018> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

set -e

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 dbname"
    exit 1
fi

origdbname="$1"
tmpdb="tmp_dump_$RANDOM"

echo -n "Creating temporary database $tmpdb mirroring $origdbname... "
createdb -T "$origdbname" "$tmpdb"
echo "done."

anonymize_field () {
    tbl="$1"
    field="$2"
    replacement="${3:-"''"}"
    echo -n "  anonymizing int field '$field'... "
    echo "update $tbl set $field = $replacement;" | psql "$tmpdb"
}

# for digest()
echo "create extension pgcrypto;" | psql --quiet "$tmpdb"

# remove NOTICE messages
export PGOPTIONS='--client-min-messages=warning'

echo
echo "Anonymizing table users_prologinuser"
anonymize_field users_prologinuser username "'user-' || CAST(id AS text)"
# Replace all passwords by "test"
anonymize_field users_prologinuser password "'pbkdf2_sha256$100000$vCF9hiF6rTDk$5Og7f4Z6hqv4onD7Y3dn8bzTsbejhN986xzZ747iMGU='"
anonymize_field users_prologinuser first_name "'Joseph'"
anonymize_field users_prologinuser last_name "'Marchand'"
anonymize_field users_prologinuser email "encode(digest(username, 'sha256'), 'hex')"
anonymize_field users_prologinuser address "'1 rue Ginette Fake'"
anonymize_field users_prologinuser postal_code "'42404'"
anonymize_field users_prologinuser city "'Donaldville'"
anonymize_field users_prologinuser country "'Syldavie'"
anonymize_field users_prologinuser phone "'0147200001'"
anonymize_field users_prologinuser gender 0
anonymize_field users_prologinuser school_stage 0
anonymize_field users_prologinuser birthday "'2000-01-01'"

echo
echo -n "Deleting all submission codes... "
echo "truncate problems_submissioncode cascade" | psql "$tmpdb"

echo -n "Deleting all djmail messages... "
echo "truncate djmail_message cascade" | psql "$tmpdb"

dump="prologin-anonymized-dump-$( date --iso-8601 ).psql"
echo -n "Dumping data to $dump... "
pg_dump -Fc --no-owner --no-privileges "$tmpdb" > "$dump"
echo "done."

echo
echo -n "Deleting temporary database $tmpdb... "
dropdb $tmpdb
echo "done."
