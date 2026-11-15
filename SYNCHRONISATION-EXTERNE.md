# Activation du déclenchement externe FFR — US Tours Rugby

> **Statut : prêt côté dépôt GitHub, activation du service externe nécessaire.**
> Notre PWA, le collecteur et GitHub Pages restent inchangés.
> **Ne jamais stocker un jeton GitHub dans ce dépôt, un ticket public, ou dans le chat.**

## Pourquoi ?

Les déclenchements `schedule` GitHub Actions peuvent arriver en retard ou être abandonnés. Le 15 novembre 2026, aucun des déclenchements rapprochés attendus n'avait été exécuté avant le début du match Espoirs. Une exécution déclenchée par un `push` a, elle, correctement collecté Courbevoie–Tours Espoirs 10–5 à 15h02.

Le workflow `.github/workflows/sync-ffr.yml` accepte déjà `workflow_dispatch` : l'API GitHub peut donc lancer le **même collecteur**, sans exposer les données ou les secrets de l'application.

## Configuration recommandée : cron-job.org + GitHub workflow_dispatch

- **Coût** : cron-job.org propose une utilisation gratuite.
- **Hébergement** : pas de NAS, pas de serveur personnel, pas de Docker.
- **Compte externe** : oui, un compte cron-job.org à créer par le propriétaire du projet.
- **Jeton** : nécessaire pour démarrer un workflow GitHub via l'API ; limiter ce jeton au dépôt `Franckmo/ust-rugby`.
- **Automatisation visée** : toutes les 5 minutes le dimanche de 13h à 20h heure de Paris, puis synchronisation de secours via les horaires GitHub existants. Cet intervalle tient compte du passage heure d'été/heure d'hiver grâce au fuseau Europe/Paris.

### Étape 1 — Jeton GitHub limité

1. Aller sur https://github.com/settings/personal-access-tokens/new
2. Choisir **Fine-grained personal access token**.
3. `Resource owner` : compte **Franckmo**.
4. `Repository access` : **Only select repositories** → **ust-rugby** seulement.
5. `Repository permissions` → **Actions: Read and write** (et aucune autre permission ajoutée sauf celles automatiquement requises par GitHub).
6. Choisir une **date d'expiration**, noter de la renouveler avant échéance.
7. Générer le jeton. Ne pas l'envoyer par message : le saisir uniquement dans la configuration privée de cron-job.org.

> Remarque sécurité : le prestataire cron-job.org conservera cet en-tête d'autorisation pour l'exécution. Il faut lui faire confiance pour protéger ce secret. Un jeton limité à un dépôt et à « Actions » est préférable à un jeton classique donnant accès à tous les dépôts.

### Étape 2 — Créer la tâche chez cron-job.org

1. Aller sur https://console.cron-job.org/ et créer/ouvrir un compte.
2. Créer une tâche : **UST Rugby — collecte FFR**.
3. **URL** :

   `https://api.github.com/repos/Franckmo/ust-rugby/actions/workflows/sync-ffr.yml/dispatches`

4. Méthode HTTP : **POST**.
5. Corps (type JSON) :

   ```json
   {"ref":"main"}
   ```

6. En-têtes personnalisés :

   | En-tête | Valeur |
   |---|---|
   | `Authorization` | `Bearer <JETON_GITHUB_PERSONNEL>` |
   | `Accept` | `application/vnd.github+json` |
   | `Content-Type` | `application/json` |
   | `X-GitHub-Api-Version` | `2022-11-28` |

7. Planning : **Europe/Paris**, jour de la semaine **dimanche**, heures **13 à 20 inclus**, minutes **00, 05, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55**. Une heure de fin 20:00 signifie ici que les appels peuvent continuer jusqu'à 20:55. Ajuster les heures si souhaité.
8. Activer la tâche et effectuer un test **manuellement** depuis cron-job.org.
9. Résultat attendu côté cron-job.org : **HTTP 204 No Content** (réponse normale pour un dispatch accepté). Cela signifie que GitHub a accepté la demande, **pas** que les données ont été collectées.
10. Vérifier le résultat dans https://github.com/Franckmo/ust-rugby/actions : nouveau workflow « Synchronisation FFR », déclencheur **workflow_dispatch**, statut **success**, puis vérifier `ffr-data.json` et l'heure de dernière collecte sur la PWA.

### Que faire en cas d'échec ?

- **401** : jeton invalide/expiré ou mauvais `Bearer`.
- **403** : permissions GitHub « Actions: write » manquantes ou accès refusé.
- **404** : erreur d'URL, dépôt non sélectionné dans le jeton, ou workflow non accessible.
- **422** : mauvais JSON, mauvaise branche ou workflow sans `workflow_dispatch`.
- **204** sans mise à jour : contrôler les logs Actions ; un workflow peut s'être lancé puis avoir échoué, ou la FFR peut n'avoir publié aucune nouvelle donnée.

## Validation à faire après activation

- Observer **plusieurs** lancements automatiques (idéalement trois) à cinq minutes d'intervalle sur un dimanche, pas seulement un test manuel.
- Vérifier la fraîcheur de `ffr-data.json` et les statuts de matchs dans la PWA.
- Vérifier que les erreurs sont visibles dans cron-job.org et dans GitHub Actions.
- **N'appeler la configuration « opérationnelle » qu'après validation**.
- Conserver provisoirement le cron natif GitHub en secours, mais ne pas compter sur lui pour un intervalle garanti.
- Ne pas lancer un deuxième scheduler tant que le premier n'a pas été désactivé.

## Références

- https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event
- https://docs.cron-job.org/rest-api.html
- https://cron-job.org/en/faq/
