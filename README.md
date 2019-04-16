# OpenPathology


OpenPathology is a new project being built by the EBM DataLab at the
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
