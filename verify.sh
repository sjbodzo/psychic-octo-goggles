# Purpose: Generates a layout as you might do in a CI pipeline but locally 
# Required env vars: 
#   GITHUB_REPOSITORY -- ref to github repo being built from
#   GITHUB_SHA -- sha of commit to base master off of
#   DOCKER_TAG -- container image ref & version to tag
#   COSIGN_PASSWORD -- key password for cosign signing key

in-toto-run -n clone --key bob -P 123 -p ${${GITHUB_REPOSITORY#*/}%.git} -- /bin/sh -c "set -x; git clone ${GITHUB_REPOSITORY} && cd ${${GITHUB_REPOSITORY#*/}%.git} && git reset --hard ${GITHUB_SHA}"
in-toto-run --key carl -P 123 -n build -m "${${GITHUB_REPOSITORY#*/}%.git}" -p build/sample -- go build -o build/sample "${${GITHUB_REPOSITORY#*/}%.git}/src/main.go"
in-toto-run --key carl -P 123 -n docker_build -m "${${GITHUB_REPOSITORY#*/}%.git}" -p ./img.tar -- docker build --file Dockerfile --tag ${DOCKER_TAG} ${${GITHUB_REPOSITORY#*/}%.git} && docker save -o img.tar $DOCKER_TAG
in-toto-run --key bob -P 123 -n sbom_gen -m "${GITHUB_REPOSITORY#*/}" -m ./img.tar -p ./sbom.json -- /bin/sh -c "syft packages docker-archive:img.tar -o cyclonedx-json > sbom.json"
in-toto-run --key bob -P 123 -n docker_push -m "${${GITHUB_REPOSITORY#*/}%.git}" -- docker push ${DOCKER_TAG}
in-toto-run --key bob -P 123 -n oci_sign -m "${${GITHUB_REPOSITORY#*/}%.git}" -p sig -- cosign sign ${DOCKER_TAG} --key ${SIGNING_KEY} --output-signature=./sig

# Assumes you have the generated layout and keys heres at your base
mkdir verify && \
    cp *.link root.layout alice.pub verify/ && \
    in-toto-verify --layout root.layout --layout-key alice.pub