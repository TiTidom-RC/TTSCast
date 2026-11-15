# Instructions Copilot — Plugin Jeedom `TTSCast`

## Contexte du projet
TTSCast est un **plugin Jeedom** de gestion des appareils Google Cast (Google Home, Nest, Chromecast). Il permet les notifications TTS (synthèse vocale), la diffusion de médias (MP3, YouTube, radio) et l'affichage de pages web (DashCast).

### Architecture
- **Stack hybride** : PHP (intégration au Core Jeedom, interface) + Python (démon de pilotage des appareils).
- **Flux de communication** :
  1. **Utilisateur / scénario** : déclenche une action dans Jeedom.
  2. **Core (`core/class/ttscast.class.php`)** : traite la demande et envoie une commande au démon via socket TCP.
  3. **Démon (`resources/ttscastd/ttscastd.py`)** : reçoit la commande, génère le TTS si besoin, et pilote l'appareil avec `pychromecast`.
  4. **Interface (`desktop/js/ttscast.js`)** : gère les interactions de l'interface et ses mises à jour via AJAX (`core/ajax/ttscast.ajax.php`).

## Environnement de développement
- **OS de développement** : Windows 11. Utiliser **PowerShell** pour les scripts locaux et les recherches dans le code (ex. `Select-String` au lieu de `grep`, `Get-ChildItem` au lieu de `find`).
- **OS cible** : Debian 12 (Jeedom). Le code du plugin doit être compatible avec les chemins et permissions Linux, même s'il est développé sous Windows.
- **Déploiement** : le code est modifié en local sous Windows puis déployé sur une instance Jeedom/Debian distante pour les tests.

## Workflow Git
- **Commits** : faits exclusivement par l'utilisateur via GitHub Desktop. Ne jamais commiter, pousser ni ouvrir de PR soi-même. En fin de tâche, lister les fichiers modifiés. Quand c'est utile pour garder des commits propres et séparés (par exemple avant d'enchaîner sur une autre tâche), signaler que c'est le bon moment pour committer, en précisant le périmètre du commit.

## Répertoires clés
- `core/class/` : logique PHP principale (`ttscast.class.php` étend `eqLogic`).
- `core/ajax/` : points d'entrée AJAX des interactions de l'interface.
- `desktop/php/` : pages de configuration du plugin et de gestion des équipements.
- `desktop/js/` : logique de l'interface (voir le pont jQuery/`CustomEvent`).
- `resources/ttscastd/` : code source et utilitaires du démon Python.
- `resources/install_apt.sh` : gestion des dépendances (`pyenv` et `venv`).

## Workflows essentiels

### Développement du démon
- Le démon Python (`ttscastd.py`) tourne en permanence.
- **Redémarrage nécessaire** : après toute modification d'un fichier Python de `resources/ttscastd/`, redémarrer le démon depuis la page de configuration du plugin dans Jeedom pour que les changements soient pris en compte.
- **Logs** : les logs Python sont écrits dans le log `ttscast_daemon` de Jeedom.

### Gestion des dépendances
- Les dépendances Python sont gérées strictement dans un environnement virtuel (`resources/venv`).
- Se référer à la logique de `resources/install_apt.sh` pour comprendre comment l'environnement est construit.
- `requirements.txt` liste les paquets Python.

### Débogage
- **PHP** : utiliser `log::add('ttscast', 'debug', 'Message');`.
- **Python** : utiliser `logging.debug("Message")`.
- **JavaScript** : les logs console sont visibles dans les outils de développement du navigateur.

## Conventions de code
- **Standards Jeedom** : respecter la structure standard d'un plugin Jeedom et l'héritage de classes (`eqLogic`, `cmd`).
- **Traductions** : utiliser `__('Texte', __FILE__)` en PHP et vérifier que les clés existent dans `core/i18n/`.
- **Événements JS** : le projet utilise un pont qui convertit les anciens événements jQuery en `CustomEvent` natifs dans `desktop/js/ttscast.js`. Conserver ce pattern.
- **Intégration GenAI** : le démon prend en charge Google GenAI (Gemini). Les imports de `google-genai` doivent être faits dans des blocs try/except.

## Patterns courants
- **Communication par socket** : le PHP envoie des messages JSON au démon Python via `jeedom_socket`.
- **Attributs** : les options de personnalisation des widgets sont définies dans `$_widgetPossibility` côté PHP.
- **Chiffrement** : les clés de configuration sensibles (comme les clés API) sont listées dans `$_encryptConfigKey`.
