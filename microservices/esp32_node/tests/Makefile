# Host-side test build for Mole.AI ESP32 Node firmware
# Usage: make test   (requires gcc + cJSON dev library)
#        make clean

CC      = gcc
CFLAGS  = -I../main/include -Wall -Wextra -Wno-unused-parameter -g -O0
LDFLAGS = -lm

# Stubs for ESP-IDF / FreeRTOS types (host-side only)
STUBS   = -Istubs

# Path to the managed cJSON source
CJSON_SRC = ../managed_components/espressif__cjson/cJSON/cJSON.c
CJSON_H   = ../managed_components/espressif__cjson/cJSON

PAYLOAD_SRC = ../main/payload_builder.c

# Payload builder tests (VS1a)
PAYLOAD_SRCS = test_payload_builder.c $(PAYLOAD_SRC) $(CJSON_SRC)
PAYLOAD_BIN  = test_payload_builder.elf

# FSM header-only tests (VS2) — implementation requires ESP-IDF stubs
FSM_SRCS  = test_state_machine.c
FSM_BIN   = test_state_machine.elf

# FSM behavioral tests (links state_machine.c via stubs)
FSM_BEH_SRCS = test_fsm_behavior.c ../main/state_machine.c stubs/main_stubs.c
FSM_BEH_BIN  = test_fsm_behavior.elf

# Offline buffer tests (pure C, no ESP-IDF stubs needed)
OFFBUF_SRCS = test_offline_buffer.c ../main/offline_buffer.c
OFFBUF_BIN  = test_offline_buffer.elf

.PHONY: test clean

test: $(PAYLOAD_BIN) $(FSM_BIN) $(FSM_BEH_BIN) $(OFFBUF_BIN)
	./$(PAYLOAD_BIN)
	./$(FSM_BIN)
	./$(FSM_BEH_BIN)
	./$(OFFBUF_BIN)

$(PAYLOAD_BIN): $(PAYLOAD_SRCS)
	$(CC) $(CFLAGS) -I$(CJSON_H) $(PAYLOAD_SRCS) $(LDFLAGS) -o $@

$(FSM_BIN): $(FSM_SRCS)
	$(CC) $(CFLAGS) $(STUBS) $(FSM_SRCS) $(LDFLAGS) -o $@

$(FSM_BEH_BIN): $(FSM_BEH_SRCS)
	$(CC) $(CFLAGS) $(STUBS) $(FSM_BEH_SRCS) $(LDFLAGS) -o $@

$(OFFBUF_BIN): $(OFFBUF_SRCS)
	$(CC) $(CFLAGS) $(STUBS) $(OFFBUF_SRCS) $(LDFLAGS) -o $@

clean:
	rm -f $(PAYLOAD_BIN) $(FSM_BIN) $(FSM_BEH_BIN)
