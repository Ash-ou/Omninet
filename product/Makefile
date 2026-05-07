# ──────────────────────────────────────────────
# Omninet — Makefile (Lab SOC)
# ──────────────────────────────────────────────
# Toutes les commandes s'exécutent depuis product/
# ──────────────────────────────────────────────

COMPOSE := docker compose -f docker-compose.yml

.PHONY: up down logs test shell status build clean help

help: ## Afficher l'aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Lancer le lab en arrière-plan
	$(COMPOSE) up -d

down: ## Arrêter le lab
	$(COMPOSE) down

logs: ## Suivre les logs du serveur SOC
	$(COMPOSE) logs -f soc

test: ## Exécuter les tests pytest dans le container
	$(COMPOSE) run --rm soc pytest tests/ -v

shell: ## Ouvrir un shell dans le container SOC
	$(COMPOSE) exec soc /bin/sh

status: ## Afficher l'état des services
	$(COMPOSE) ps

build: ## Reconstruire les images
	$(COMPOSE) build

clean: ## Arrêter et supprimer containers + images + volumes
	$(COMPOSE) down --rmi local --volumes
