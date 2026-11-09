# CLAUDE.md

Les instructions de ce dépôt sont maintenues dans un fichier unique, partagé avec Copilot :

@.github/copilot-instructions.md

## Compatibilité PHP

- Le code doit fonctionner en PHP 7.4 (Debian 11), 8.2 (Debian 12) et 8.4 (Debian 13). Debian 11 est en fin de vie : la compatibilité 7.4 est maintenue par choix, le temps que les utilisateurs migrent leur Jeedom vers Debian 12 minimum. Aucune syntaxe ni fonction propre à PHP 8.x.
- La CI (`checkPHPCompat.yml`, PR vers `beta`) analyse `core/`, `desktop/` et `plugin_info/` avec PHPStan niveau 0 en PHP 7.4, 8.2 et 8.4.
- Le poste de dev tourne en PHP 8.4, la version la plus haute, pour faire apparaître les régressions et les `Deprecated` (installation : `../Documentation/_docs/php-windows-dev.md`).
