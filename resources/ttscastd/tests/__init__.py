import logging

# Sans gestionnaire, Python écrit les logs de niveau WARNING et plus sur la sortie d'erreur (logs attendus du démon pendant les tests) :
# un gestionnaire neutre les fait taire. Les tests qui vérifient des logs les capturent eux-mêmes (assertLogs, LoggingTestCase)
logging.getLogger().addHandler(logging.NullHandler())
