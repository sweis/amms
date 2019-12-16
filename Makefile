PROTOC = protoc
PYTHON = python3
PROTO_OPTIONS = amms_proto.options
BUILD_DIR = pb
PYCACHE = __pycache__
TEST_DIR = tests
TEST_SUFFIX = _test.py
PROTOS = $(wildcard *.proto)
PROTO_PB = $(patsubst %.proto, $(BUILD_DIR)/%_pb2.py,$(PROTOS))
RMRF = rm -Rf

all: test

$(PROTO_PB): $(BUILD_DIR) $(PROTOS)
	$(PROTOC) @$(PROTO_OPTIONS) $(PROTOS)

$(BUILD_DIR):
	mkdir $(BUILD_DIR)

test: $(PROTO_PB)
	$(PYTHON) -m unittest discover $(TEST_DIR)/ "*$(TEST_SUFFIX)"

clean:
	$(RMRF) $(BUILD_DIR)/*
	$(RMRF) $(TEST_DIR)/$(PYCACHE)
	$(RMRF) $(PYCACHE)
