# CLAUDE.md

> Pendant de `.github/copilot-instructions.md` (instructions Copilot) : toute règle commune ajoutée ou modifiée ici est à reporter là-bas, et inversement.

## Contexte

Plugin Jeedom **TTSCast** : pilotage des appareils Google Cast (Google Home, Nest, Chromecast). Notifications TTS (synthèse vocale), diffusion de médias (MP3, YouTube, radio), affichage de pages web (DashCast). Intègre Google GenAI (Gemini).

Stack hybride PHP + démon Python :

1. Un utilisateur ou un scénario déclenche une action dans Jeedom.
2. `core/class/ttscast.class.php` (étend `eqLogic` / `cmd`) traite la demande et l'envoie au démon par socket TCP (messages JSON, `jeedom_socket`).
3. Le démon `resources/ttscastd/ttscastd.py` génère le TTS si besoin et pilote l'appareil avec `pychromecast`. Il remonte ses événements à Jeedom par HTTP vers `core/php/jeettscast.php`.
4. L'interface (`desktop/php/`, `desktop/js/ttscast.js`) dialogue avec `core/ajax/ttscast.ajax.php`.

Autres fichiers : `core/php/ttscast.audio.proxy.php` et `ttscast.img.proxy.php` (proxys audio / image), `resources/install_apt.sh` (pyenv + venv), `resources/requirements.txt` (+ `requirements-piper.txt`).

## Environnement

- Dev : Windows 11, PowerShell 7. Utiliser l'outil **PowerShell** (pas Bash) pour les commandes ; les outils Grep/Glob pour chercher dans le code. Toute commande proposée à l'utilisateur est en PowerShell. Les scripts `.sh` du repo s'exécutent sur la cible et restent en bash.
- Cible : Jeedom sur Debian 11/12/13. Le code doit respecter chemins et permissions Linux, même écrit sous Windows. Aucun Jeedom local : le code est déployé sur une box distante pour être testé ; signaler ce qui reste à y vérifier.
- Python : 3.12 via pyenv, environnement virtuel `resources/venv` sur la cible (voir `install_apt.sh`). En local, utiliser le `.venv` à la racine du repo, jamais le Python système.
- Toute modification d'un fichier de `resources/ttscastd/` ne prend effet qu'après redémarrage du démon depuis la page de configuration du plugin : le rappeler à l'utilisateur.

## Tests et lint

- Tests du démon : `python -m unittest discover -s tests -t .` depuis `resources/ttscastd`, avec le Python du `.venv`. Ajouter ou adapter les tests de `resources/ttscastd/tests/` avec chaque correctif ou fonctionnalité du démon.
- Lint Python : Ruff (`ruff.toml`), comme la CI (`ruff check resources/ttscastd/`).

## Workflow Git

- **Commits** : faits exclusivement par l'utilisateur via GitHub Desktop. Ne jamais commiter, pousser ni ouvrir de PR soi-même. En fin de tâche, lister les fichiers modifiés. Quand c'est utile pour garder des commits propres et séparés (par exemple avant d'enchaîner sur une autre tâche), signaler que c'est le bon moment pour committer, en précisant le périmètre du commit.
- Branches : `dev` → PR vers `beta` → stable. La CI tourne sur les PR vers `beta`.
- `core/i18n/*.json` est généré par le workflow `translations.yml` : ne jamais l'éditer à la main.

## Compatibilité PHP

- Le code doit fonctionner en PHP 7.4 (Debian 11), 8.2 (Debian 12) et 8.4 (Debian 13). Debian 11 est en fin de vie : la compatibilité 7.4 est maintenue par choix, le temps que les utilisateurs migrent leur Jeedom vers Debian 12 minimum.
- Aucune syntaxe ni fonction propre à PHP 8.x : `str_starts_with`/`str_ends_with`/`str_contains` (→ `strpos`/`substr`), `match` (→ `switch`), named arguments, `enum`, `readonly`, `fibers`, union types (→ docblock `@param`). Les arrow functions `fn()` sont autorisées (PHP 7.4).
- La CI (`checkPHPCompat.yml`, PR vers `beta`) analyse `core/`, `desktop/` et `plugin_info/` avec PHPStan niveau 0 en PHP 7.4, 8.2 et 8.4.
- Le poste de dev a PHP 8.4 dans le PATH, pour faire apparaître les régressions et les `Deprecated` (installation : `../Documentation/_docs/php-windows-dev.md`). Contrôle après modification, depuis la racine du repo :

  ```powershell
  Get-ChildItem core, desktop, plugin_info -Recurse -Filter *.php |
      ForEach-Object { php -l $_.FullName 2>&1 } |
      Where-Object { $_ -notmatch '^No syntax errors' }
  ```

## Conventions et patterns

- Respecter la structure standard d'un plugin Jeedom et l'héritage `eqLogic` / `cmd`. Ne jamais réimplémenter une fonction du Core : chercher d'abord dans `../Jeedom/core`.
- Logs : `log::add('ttscast', 'debug', '...')` en PHP, `logging.debug(...)` dans le démon (log Jeedom `ttscast_daemon`).
- Traductions : `__('Texte', __FILE__)` en PHP, en français uniquement.
- Options de widget : `$_widgetPossibility`. Clés de configuration sensibles (clés API) : à déclarer dans `$_encryptConfigKey`.
- JavaScript : `desktop/js/ttscast.js` convertit les événements jQuery du Core en `CustomEvent` natifs (pont à sens unique). Conserver ce pattern et écrire le nouveau code en vanilla JS.
- GenAI : SDK `google-genai` (`from google import genai`), jamais l'ancien `google-generativeai`. Import dans un `try/except ImportError` sans arrêter le démon : la fonctionnalité est optionnelle.
- Nouvelle dépendance Python : `resources/requirements.txt`, uniquement après accord de l'utilisateur.

## Documentation utilisateur (repo voisin `../Documentation`, branche `beta`)

- Changelog stable : `../Documentation/fr_FR/TTSCast/changelog.md` ; beta : `../Documentation/fr_FR/TTSCast/beta/changelog.md` ; doc : `../Documentation/fr_FR/TTSCast/index.md`.
- Format et ton : voir `../Documentation/CLAUDE.md`. Commits séparés de ceux de ce repo.
