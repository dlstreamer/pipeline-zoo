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
rm -rf .staging

git clone https://github.com/intel-innersource/frameworks.ai.media-analytics.pipeline-zoo.git .staging

cd .staging

git checkout origin/main
git branch -D public-updates || true
git checkout -b public-updates

git filter-repo --refs public-updates --paths-from-file $SOURCE_DIR/.public.txt --force
git filter-repo --refs public-updates --paths-from-file $SOURCE_DIR/.internal.txt --force --invert

#git add --all

#git commit -m "adding new files"

git checkout public-main
git reset --hard origin/public-main

git merge public-updates --squash --allow -X theirs
git rm -rf .
git checkout public-updates -- .
git commit --no-edit


MESSAGE=$1
if [ -z "$1" ]; then
    MESSAGE="updates to public"
fi

#git commit -m "$MESSAGE"
#git commit --no-edit

git push origin public-main:public-staging --force
#git branch -D public-updates

# git checkout main
