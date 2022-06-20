# CAP Pipeline: Preparing datadumps (cap--pipeline-dumps)

The dumps pipeline access the triple store to obtain data dumps. Then it transforms and enriches for ingestion to production services, in our case solr. Output of this pipeline is indexed and kept with solr
