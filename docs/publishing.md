# Publishing to the Public Pipeline Zoo

The pipeline zoo repositories:

* pipeline-zoo-models
* pipeline-zoo-media
* pipeline-zoo

Are designed to have internal and public versions. All files that are to be published or removed are listed in: 

```
manifest/public.txt
manifest/internal.txt
```

The script ``update-public.sh`` is provided to help automate the following procedure:

1. Create a clean staging area
2. Use git-filter-repo to remove all files not listed in public.txt
3. Use git-filter-repo to remove all files listed in internal.txt
4. Pull the latest public main and push internally to public-main (in case they are out of sync)
5. Create a branch called public-staging with all changes against public-main

Once these steps are complete you'll have a `public-main` and `public-staging`. Create a PR from `public-main` to `public-staging` to be able to review changes.

Once ready push from the internal public-staging to the public repo. 

Create a PR from public-staging to main and commit.

Manual testing should be done now - and be done without access to inner-source.

## Special Note for Models and Media

Models and media are slightly different because the internal repositories use git-lfs while the public ones do not. (We ran into data transfer limits with git-lfs in the public repo).

Thus the scripts there follow the same procedure but push the public-staging to the public-repo directly.
