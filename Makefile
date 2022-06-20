
# Building docker image
VERSION = "v0.0.1"
IM=matentzn/vfb-pipeline-dumps
OUTDIR=~/data/vfb
# SPARQL_ENDPOINT=http://ts.p2.virtualflybrain.org/rdf4j-server/repositories/vfb

docker-build-no-cache:
	@docker build --no-cache -t $(IM):$(VERSION) . \
	&& docker tag $(IM):$(VERSION) $(IM):latest

docker-build:
	@docker build -t $(IM):$(VERSION) . \
	&& docker tag $(IM):$(VERSION) $(IM):latest

docker-run:
	docker run --volume $(OUTDIR):/out --env=ROBOT_JAVA_ARGS='-Xmx8G' $(IM)

docker-clean:
	docker kill $(IM) || echo not running ;
	docker rm $(IM) || echo not made

docker-publish-no-build:
	@docker push $(IM):$(VERSION) \
	&& docker push $(IM):latest

docker-publish: docker-build-use-cache
	@docker push $(IM):$(VERSION) \
	&& docker push $(IM):latest

#include dumps.Makefile
