
TARGET_OS=linux
SHELL_GET_TARGET_ARCH := $(shell test ! -z $(TARGET_ARCH) && echo $(TARGET_ARCH) || \
	arch \
	| sed s/x86_64/amd64/g \
	| sed s/i386/amd64/g \
	| sed s/aarch64/arm64/g \
)
TARGET_TAG=$(TARGET_OS)-$(SHELL_GET_TARGET_ARCH)
CONTAINER_NAME=labop
TAGGED_NAME=$(CONTAINER_NAME):$(TARGET_TAG)
REGISTRY_ROOT=danbryce

docker:
	DOCKER_BUILDKIT=1 docker buildx build \
		--output "type=docker" \
		--platform $(TARGET_OS)/$(SHELL_GET_TARGET_ARCH) \
		-t ${TAGGED_NAME} -f ./Dockerfile .
	docker tag $(TAGGED_NAME) $(REGISTRY_ROOT)/$(TAGGED_NAME)
	docker push $(REGISTRY_ROOT)/$(TAGGED_NAME)

run: docker
	docker run \
		-it \
		--rm \
		--name ${CONTAINER_NAME} \
		-v $$PWD:/root/home:Z \
		-e "PROTOCOL_SCRIPT=${PROTOCOL_SCRIPT}" \
		${TAGGED_NAME}

spec:
	python doc/generate_specification_content.py

lib-docs:
	mkdocs build

test:
	pytest test
	pytest --nbmake --overwrite -n=auto "notebooks/labop_demo.ipynb" "notebooks/markdown.ipynb"

format:
	pre-commit
