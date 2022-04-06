# OpenPathology


OpenPathology is a new project being built by the Bennett Institute for Applied Data Science at the
University of Oxford.

This repo is the code related to the website at https://openpathology.net.

The code for related research is in its [own repository](https://github.com/ebmdatalab/openpathology-web).


## Aims and objectives

Our single aim is to create an innovative high impact pathology benchmarking tool that improves patient care, using advanced “data science” “under the bonnet” to give GPs simple, actionable insights.

This will be achieved through completing the following objectives:

- Build infrastructure to securely import, store and analyse pathology datasets
- Normalise the data
- Create a website to appropriately display data on testing rates for each major test type
- Create standard measures with clinicians
- Deploy and iteratively improve throughout agile development cycles.

Clinicians currently receive almost no feedback on their test request rates, or how these relate to national norms. Our live, up-to-date pathology monitoring tool will show clinicians and policy-makers how recent testing rates and performance on specific measures of pathology test appropriateness compare with other practices. This will highlight areas requiring further investigation to improve patient care. It will also give live data on overall trends in test use over time for policymakers, commissioners and researchers.

The motivation is further explained
in [our paper](https://www.nature.com/articles/s41598-018-23263-z) on
the subject.

## More information
Please see [our website](https://openpathology.net)

# Development

This is a Django app.  Deployment is managed via Heroku.  A fresh instance can be deployed thus:

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

A development sandbox can be run by copying `env-sample` to `.env` and updating the details.  You will also need to create a postgres database. You can then either use the usual Django tooling, or use `heroku local` to run a server.

## Deploying to Dokku

Follow "first time" instructions below, then deploys are handled by

```sh
git push dokku master
```

### First time

On the server:

```sh
dokku plugin:install https://github.com/dokku/dokku-postgres.git
dokku apps:create openpathology-web
dokku config:set openpathology-web SECRET_KEY=xxx
dokku postgres:create openpathology
dokku postgres:link openpathology openpathology-web
```

ufw allow in on eth0 from 192.168.0.0/16

On a checkout (e.g. dev machine):

```sh
git remote add dokku dokku@dokku.ebmdatalab.net:openpathology-web
```

### Blog entries

Rather than managing a blog on this website, we pull in HTML content from other websites (specifically, our main datalab website), and present them here.

To add a blog page, edit the file at `frontend/management/commands/blog_entries.yaml`, then run `./manage.py fetch_blog_entries` and commit the newly-created HTML that results.

### Prototype measures

These are generated by hand from Jupyter Notebooks and have the filename structure `<measure_id>_<ods_practice_code>_<sort_key>.png`.

A user who visits `/measure/<measure_id>` will see all the charts whose filename starts `<measure_id>`

A user who visits `/measure/<measure_id>?filter=ods/13T` will see all the charts whose filename starts `<measure_id>` and whose practice or grouping matches the code `ods/13T`. A practice can have several codes or groupings; so `/measure/<measure_id>?filter=ods/L82008` will show the chart for that practice only, whereas if `ods/13T` is a group, it will show all the practices in that group.

Groups currently supported by the import process are CCGs and Labs.  These (along with practice codes) are imported with:

    ./manage.py import_practices --filename=data/practices_for_website_anonymised.csv

Or, to do the same in the dokku container:

    ssh -t dokku@dokku.ebmdatalab.net run openpathology-web python manage.py import_practices --filename=data/practices_for_website_anonymised.csv

The ODS code for the practice is used as the key, so importing practices will also do an update operation for existing practice codes.

Measures currently only have  `id`, `title`, and `why_it_matters` fields. These can be imported with:

    ./manage.py import_measures --filename=data/measures.csv

This is also an update operation for measures with existing ids.
