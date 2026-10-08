# nothing dotfiles — common tasks.  `make` lists them.
.DEFAULT_GOAL := help
SHELL := /usr/bin/env bash

.PHONY: help install links dry-run check selftest reload update

help: ## Show this help
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[1m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Full install: packages, system settings, fonts, symlinks
	./install.sh

links: ## Only (re)create the symlinks — no sudo
	./install.sh --links-only

dry-run: ## Show everything install would do, change nothing
	./install.sh --dry-run

check: ## Lint shell/python/json and verify hyprland.lua
	./scripts/check.sh

selftest: ## Click every control in the Settings app (needs a running Hyprland; changes nothing)
	NOTHING_SETTINGS_SELFTEST=1 ./settings/nothing-settings.py

reload: ## Reload the running desktop (Hyprland, island, bars, wallpaper)
	./hypr/scripts/nothing-reload.sh

update: ## Pull the latest version and relink
	git pull --ff-only && ./install.sh --links-only
