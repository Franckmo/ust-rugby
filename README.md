# US Tours Rugby — Référence du projet

> **Document de référence inter-conversations — dernière mise à jour : 8 novembre 2026.**  
> Pour reprendre le projet dans une autre conversation, lire **ce README**, puis les fichiers du dépôt GitHub. Ne pas supposer que l'état d'une conversation précédente est toujours actuel : vérifier le code et les derniers workflows.

## Accès et hébergement

- **Dépôt GitHub** : https://github.com/Franckmo/ust-rugby
- **Application publiée** : https://franckmo.github.io/ust-rugby/
- **Type** : PWA (Progressive Web App) mobile Android et ordinateur ; installable depuis Chrome, sans Play Store.
- **Hébergement** : GitHub Pages, branche `main`, racine `/`. **Aucune dépendance au NAS**, à Docker ou à Arcadia.
- **Identité** : US Tours Rugby (UST), interface bleu marine / orange.

## Fonctionnalités présentes

1. Choix **Seniors (Fédérale 1, poule 1)** ou **Espoirs (Espoirs Fédéraux, poule 1)**.
2. **Classement** complet, rang de l'US Tours, points, bilan et rang des adversaires **entre parenthèses** sur les rencontres.
3. **Calendrier** avec indication domicile (stade Tonnellé) / extérieur, date, horaire indicatif et filtres.
4. **Résultats** des matchs passés avec scores et indication victoire/défaite.
5. **Statut et score du match du jour directement sur sa carte** : « En direct FFR », « Terminé » ou état non confirmé. L'application ne doit jamais inventer un score.
6. Affichage des données FFR disponibles, de la **date de collecte sur le serveur** et de l'**heure de consultation sur le téléphone** (ce ne sont pas les mêmes heures). Bouton « Recharger les données » ; si le serveur n'a pas de nouveau relevé, le dire clairement.
7. Cache PWA et **données de secours** si la FFR est indisponible : ne jamais faire disparaître un calendrier ou un classement valide à cause d'une collecte ratée.

## Architecture et source des données

```text
FFR Mon Club House (pages compétitions + multiplex « Matchs en direct »)
    ↓
GitHub Actions : .github/workflows/sync-ffr.yml
    ↓
Python + Playwright : scripts/sync_ffr.py
    ↓
ffr-data.json (dans la branche main)
    ↓
GitHub Pages : index.html + manifest.webmanifest + sw.js + icon.svg
    ↓
PWA installée sur Android / navigateur desktop
```

- **Source de référence** : FFR Mon Club House, à privilégier pour classement, calendrier, scores.
- **Scores en direct** : page `https://monclubhouse.ffr.fr/rugby-direct` → onglet **Tous les matchs** → **Compétitions Nationales** → **Fédérale 1** ; contenu dynamique, ouverture par Playwright.
- **Compétitions** : `https://monclubhouse.ffr.fr/nationales/federale-1` (Seniors) et `https://monclubhouse.ffr.fr/competitions/espoirs-federaux` (Espoirs).
- Le script ne marque un score « live » que si la FFR affiche expressément **En direct**. Le score reste **quasi-direct**, pas en temps réel seconde par seconde.
- **Automatisation** : vérifications journalières aux horaires UTC `07:15`, `12:15`, `19:15`, et **toutes les 5 minutes le dimanche de 12:00 à 19:59 UTC** pendant les rencontres. Les horaires GitHub Actions sont indicatifs : GitHub peut différer des exécutions.
- La PWA consulte le JSON à l'ouverture, automatiquement environ toutes les 2 minutes quand elle est visible, et lors de l'appui sur « Recharger les données ». **Ce bouton ne déclenche pas un nouveau workflow GitHub** ; il interroge le dernier JSON publié.
- Une FFR indisponible, un JSON incomplet ou une ancienne version ne doivent pas effacer des données déjà valides. Les mises à jour de fichiers doivent préserver le fonctionnement de l'application.

## Historique vérifié — 8 novembre 2026

- Premier dépôt public GitHub et installation Android PWA opérationnels.
- Synchronisation FFR initialement bloquée par un conflit de `git push` : corrigée avec `fetch`/`rebase`/nouvelle tentative.
- Une régression JavaScript avait fait disparaître les listes de matchs ; corrigée. **Règle projet : préserver l'existant fonctionnel avant toute nouvelle fonctionnalité.**
- Match Seniors **US Tours – US Montmélianaise**, au stade Tonnellé : le multiplex officiel a été récupéré à **26–13 « En direct »** lors d'un relevé vers **16h28 heure de Paris**. Ce résultat était **provisoire**, pas un score final.
- Match Espoirs **US Tours – Montmélian : 24–10**, marqué « Terminé » dans la FFR.
- Les données du 8 novembre ne sont **pas** des classements définitifs pour toute la saison ; consulter `ffr-data.json` pour la dernière collecte.
- L'utilisateur a assisté physiquement au match à Tonnellé et a confirmé que l'application fonctionnait sur son téléphone.

## Règles de développement

- Conserver **Seniors / Espoirs + Calendrier / Classement / Résultats** dans une même application.
- L'affichage du **direct doit rester dans la carte de la rencontre du jour**, pas dans un bloc séparé qui fait doublon.
- Afficher le **score seulement s'il provient d'une source vérifiée** ; si le relevé est ancien, remplacer « En direct » par « Dernier score connu ».
- Ne pas confondre « téléphone a rechargé le JSON à 16h36 » et « FFR a été interrogée à 16h28 ». Le bouton de relecture ne force pas un nouveau prélèvement de la FFR.
- Aucune dépendance à un NAS ; ne pas proposer d'installation NAS, Docker, Home Assistant ou SSH pour ce projet.
- Ne jamais déclarer un correctif opérationnel sans vérifier la publication GitHub Pages et les **runs GitHub Actions**. Vérifier au moins le dernier fichier `ffr-data.json` et les journaux en cas de problème.
- Mettre à jour ce README à chaque étape importante, pour que les futures conversations puissent reprendre le travail au même niveau.

## À poursuivre / contrôles

- Vérifier durablement la détection de **fin de match**, la disparition de l'indication « direct » et l'apparition du résultat final.
- Contrôler les écarts éventuels de calendrier/score entre les pages de compétition et le multiplex FFR.
- Contrôler les mises à jour réelles des rangs et bilans, et les particularités des égalités de points.
- Tester les transitions de cache de la PWA sur Android, et le passage de la FFR indisponible à disponible.
- Envisager plus tard des notifications, uniquement si demandées et après validation de la fiabilité des données.

## Reprise rapide pour une nouvelle conversation

> « Reprends le projet US Tours Rugby depuis `Franckmo/ust-rugby`. Lis le README comme référence, examine `index.html`, `scripts/sync_ffr.py`, `.github/workflows/sync-ffr.yml` et le dernier `ffr-data.json`. Vérifie le dernier état GitHub Actions avant toute modification. Préserve systématiquement les fonctionnalités existantes. »

## Diagnostic et correction de la mise à jour — 8 novembre 2026, soirée

- **Problème observé** : entre environ 16h38 et 20h, aucun nouveau `ffr-data.json` publié ; le score 33–13 restait marqué `live` malgré la fin du match. Les synchronisations sur `push` avaient réussi, mais aucune exécution planifiée (`schedule`) n'était visible dans l'historique GitHub durant cet intervalle.
- **Correction apportée** : déplacer les cron hors des minutes rondes (dimanche `2-59/5 12-19 * * 0`, et horaires quotidiens minute 17), car les déclenchements planifiés GitHub peuvent être retardés ou ignorés. **Cela n'est pas encore une garantie : vérifier de vraies exécutions de type `schedule` avant de considérer le direct autonome comme fiable.**
- **Sécurité côté application** : afficher un avertissement « Données anciennes » au-delà de 15 minutes depuis la dernière collecte FFR ; un statut `live` de plus de 15 minutes devient « Dernier score connu » plutôt que « En direct ».
- **Test après correctif** : workflow `42513061831` exécuté avec succès par déclenchement `push`, fichier `ffr-data.json` mis à jour à `2026-11-08T19:03:56Z`.
- **Score FFR récupéré à ce moment-là** : Seniors Tours–Montmélian **43–18 terminé** (Tours 33 points / 8 matchs), Espoirs **24–10 terminé** (Tours 18 points / 8 matchs). Une source tierce indiquait 44–18 ; **ne pas confondre cette divergence avec la source officielle FFR**.
- **Point restant à surveiller** : les exécutions planifiées doivent se déclencher réellement les jours suivants. Le bouton « Recharger les données » lit le fichier publié ; il ne déclenche pas lui-même un nouveau relevé FFR.
