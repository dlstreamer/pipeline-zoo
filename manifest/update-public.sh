#!/bin/bash -e
#
# Copyright (C) 2019-2021 Intel Corporation.
#
# SPDX-License-Identifier: MIT
#

MANIFEST_DIR=$(dirname "$(readlink -f "$0")")
SOURCE_DIR=$(dirname $MANIFEST_DIR)
BRANCH=main

cp $SOURCE_DIR/manifest/public.txt $SOURCE_DIR/.public.txt
cp $SOURCE_DIR/manifest/internal.txt $SOURCE_DIR/.internal.txt
rm -rf .staging

# Create staging area

git clone https://github.com/intel-innersource/frameworks.ai.media-analytics.pipeline-zoo.git .staging

cd .staging

git checkout origin/$BRANCH
git branch -D public-updates || true
git checkout -b public-updates

# Explicitly keep files and directories listed in public.txt (rewrite history for public-updates)
git filter-repo --refs public-updates --paths-from-file $SOURCE_DIR/.public.txt --force

# Explicitly remove files and directories listed in internal.txt (rewrite history for public-updates)
git filter-repo --refs public-updates --paths-from-file $SOURCE_DIR/.internal.txt --force --invert

# Add public remote
git remote rm public-origin || true
git remote add public-origin https://github.com/dlstreamer/pipeline-zoo.git
git fetch public-origin

# Reset public-main to main of public-origin
# Push to origin
git checkout -b public-main
git reset --hard public-origin/main
git push --force origin public-main

# Merge public-updates ontop of public-main
git merge public-updates --squash --allow -X theirs
git rm -rf .
git checkout public-updates -- .
git commit --no-edit

MESSAGE=$1
if [ -z "$1" ]; then
    MESSAGE="updates to public"
fi

# Force updates to public-staging

git push origin public-main:public-staging --force

# After verified can do
# git push public-origin public-staging:public-staging
# merge from public github
