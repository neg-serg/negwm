#!/usr/bin/env jq
module {
	"name": "i3"
};

def windows:
	.nodes + .floating_nodes | .[] |
	if .type == "output" then
		{"output": .name} * windows
	elif .type == "workspace" then
		{"workspace": .name} * windows
	elif .nodes | length != 0 then
		windows
	else
		.
	end;

# Usage:
# windows({"name": $ws1, "type": "workspace"})
def windows(m):
	.nodes + .floating_nodes | .[] |
	if contains(m) then
		windows
	elif .nodes + .floating_nodes | length != 0 then
		windows(m)
	else
		empty
	end;

# Usage: i3-msg -t subscribe -m '["binding"]' | ... | xargs -n 2 notify-send
def print_binds:
	select(.change == "run").binding |
	.command , (.event_state_mask + .symbols | join("+"));
