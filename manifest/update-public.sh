#!/bin/bash -e
#
# Copyright (C) 2019-2021 Intel Corporation.
#
# SPDX-License-Identifier: MIT
#

MANIFEST_DIR=$(dirname "$(readlink -f "$0")")
SOURCE_DIR=$(dirname $MANIFEST_DIR)

cp $SOURCE_DIR/manifest/public.txt $SOURCE_DIR/.public.txt
cp $SOURCE_DIR/manifest/internal.txt $SOURCE_DIR/.internal.txt

git checkout origin/main
git branch -D public-updates || true
git checkout -b public-updates

git filter-repo --refs public-updates --paths-from-file $SOURCE_DIR/.public.txt --force
git filter-repo --refs public-updates --paths-from-file $SOURCE_DIR/.internal.txt --force --invert

git checkout public-init

git merge public-updates --squash --allow -X theirs

git commit -m "updates to public"

git push origin public-init:public-init

git branch -D public-updates

git checkout main
