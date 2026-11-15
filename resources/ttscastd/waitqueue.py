""" File d'attente des notifications, une par équipement (UUID canonique) : TTS, sons et médias passent un par un, dans l'ordre d'arrivée.

- Notification sans option : un ticket, servi dans l'ordre d'arrivée.
- Option « wait » : les notifications d'un même processus PHP (PID) forment un bloc, qui prend une seule place dans la file ; à l'intérieur,
  l'ordre suit la valeur de « wait » (puis l'ordre d'arrivée à valeur égale), quel que soit l'ordre d'arrivée réel.
- Option « force » : passe devant tout le monde, sans prendre de place ; la file est gelée tant qu'un « force » est en cours. À son
  tour, la notification qui occupait l'équipement est abandonnée si elle n'avait pas lancé sa diffusion ; la diffusion en cours est
  coupée et le « force » attend la sortie de la notification coupée.

Une notification en attente n'est jamais abandonnée tant que la file avance : seule une attente plus longue que l'âge maximal (queueMaxAge)
l'écarte. Chaque notification qui occupe l'équipement déclare son étape et une échéance (setPhase / phase / progress) ; une notification
en attente qui constate une échéance dépassée déclare la notification bloquée orpheline et la file passe à la suivante. Une notification
orpheline ne doit plus rien faire sur l'enceinte (isOrphaned) ; sa sortie tardive est ignorée.

Aucune dépendance à pychromecast ni à Jeedom : le module se teste avec une horloge simulée (paramètres now / clock / sleep). """

import logging
import threading
import time

PREPARING = 'preparing'  # enregistrée, préparation en cours (reformulation IA…) avant l'attente du tour
READY = 'ready'  # prête, attend son tour
ACTIVE = 'active'  # occupe l'équipement
DONE = 'done'
ABANDONED = 'abandoned'  # attente plus longue que l'âge maximal
ORPHANED = 'orphaned'  # déclarée bloquée par la file
FINISHED = (DONE, ABANDONED, ORPHANED)

LAUNCHED_PHASES = ('lancement', 'lecture', 'fin')  # étapes à partir desquelles la notification agit sur l'enceinte

_local = threading.local()


def current():
    """ Notification qui occupe l'équipement depuis le thread courant (None hors file d'attente) """
    return getattr(_local, 'ticket', None)


def _setCurrent(ticket):
    _local.ticket = ticket


def phase(name, seconds, now=None):
    """ Étape de la notification du thread courant, à terminer dans seconds secondes (marge comprise ensuite) """
    ticket = current()
    if ticket is not None:
        ticket.setPhase(name, seconds, now)


def progress(seconds, now=None):
    """ La notification du thread courant progresse : son échéance est repoussée de seconds secondes """
    ticket = current()
    if ticket is not None:
        ticket.progress(seconds, now)


def isOrphaned():
    """ True si la notification du thread courant a été déclarée bloquée : elle ne doit plus agir sur l'enceinte """
    ticket = current()
    return ticket is not None and ticket.state == ORPHANED


class Ticket:
    def __init__(self, queue, kind, number, callerName, now, waitValue=None, block=None, seq=0):
        self.queue = queue
        self.kind = kind  # 'auto', 'wait' ou 'force'
        self.number = number  # place dans la file (celle du bloc pour 'wait', None pour 'force')
        self.callerName = callerName
        self.arrival = now
        self.waitValue = waitValue
        self.block = block
        self.seq = seq
        self.order = len(block.members) + 1 if block is not None else None  # rang d'arrivée dans le bloc (logs)
        self.state = ACTIVE if kind == 'force' else PREPARING
        self.phase = None
        self.lastActivity = now
        self.deadline = None
        self.streamAudioSeconds = None  # durée de l'audio d'un flux live (Gemini en streaming), renseignée par le thread du flux à la fin de l'envoi
        self.streamEndedAt = None  # fin de l'envoi de ce flux, renseignée après streamAudioSeconds

    def label(self):
        if self.kind == 'force':
            return 'force'
        if self.kind == 'wait':
            return f'ticket {self.number} (wait={self.waitValue} #{self.order})'
        return f'ticket {self.number}'

    def setPhase(self, name, seconds, now=None):
        """ Étape name (None : étape inchangée) à terminer dans seconds secondes ; sans effet si la notification est sortie """
        with self.queue.lock:
            if self.state not in FINISHED:
                self.queue._setPhase(self, self.phase if name is None else name, seconds, time.monotonic() if now is None else now)

    def progress(self, seconds, now=None):
        """ La notification progresse : échéance repoussée de seconds secondes, étape inchangée """
        self.setPhase(None, seconds, now)


class Block:
    """ Notifications « wait » d'un même PID : une seule place dans la file, ordre interne par valeur de wait """
    def __init__(self, number, pid):
        self.number = number
        self.pid = pid
        self.members = []

    def finished(self):
        return bool(self.members) and all(m.state in FINISHED for m in self.members)

    def activeMember(self):
        return next((m for m in self.members if m.state == ACTIVE), None)

    def nextMember(self):
        pending = [m for m in self.members if m.state not in FINISHED]
        return min(pending, key=lambda m: (m.waitValue, m.seq)) if pending else None


class DeviceQueue:
    """ config : objet portant queueMaxAge, queueStallMargin et queuePrepTimeout (secondes) """
    def __init__(self, uuid, config):
        self.uuid = uuid
        self.config = config
        self.lock = threading.Lock()
        self.tail = 0  # prochaine place à attribuer
        self.serving = 0  # place servie
        self.units = {}  # place -> Ticket ('auto') ou Block
        self.blocksByPid = {}  # pid -> place du bloc ouvert
        self.forces = []
        self._seq = 0

    # ── Enregistrement (boucle socket) ───────────────────────────────────────

    def register(self, kind, callerName, now=None, waitValue=None, pid=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            if kind == 'force':
                ticket = Ticket(self, 'force', None, callerName, now)
                self.forces.append(ticket)
            elif kind == 'auto':
                ticket = Ticket(self, 'auto', self.tail, callerName, now)
                self.units[self.tail] = ticket
                self.tail += 1
            else:
                block = self.units.get(self.blocksByPid.get(pid, -1))
                if not isinstance(block, Block) or block.finished():
                    block = Block(self.tail, pid)
                    self.units[self.tail] = block
                    self.blocksByPid[pid] = self.tail
                    self.tail += 1
                self._seq += 1
                ticket = Ticket(self, 'wait', block.number, callerName, now, waitValue, block, self._seq)
                block.members.append(ticket)
            self._setPhase(ticket, 'préparation', self.config.queuePrepTimeout, now)
        return ticket

    def isActive(self):
        """ File occupée (place en attente ou en cours, ou « force » en cours) : utilisé pour relier un membre et son groupe """
        return self.tail > self.serving or any(f.state not in FINISHED for f in self.forces)

    # ── Attente du tour (thread de la notification) ──────────────────────────

    def hold(self, ticket, clock=time.monotonic, sleep=time.sleep, cut=None):
        """ Attend le tour de ticket. True : la notification occupe l'équipement ; False : abandonnée (âge) ou orpheline.
        cut : coupure de la diffusion en cours sur l'enceinte, appelée au tour d'un « force » """
        tag = f'[DAEMON][WaitQueue][{ticket.callerName}]'
        if ticket.kind == 'force':
            return self._holdForce(ticket, tag, clock, sleep, cut)
        with self.lock:
            if ticket.state == PREPARING:
                ticket.state = READY
            depth = ticket.number - self.serving
        logging.debug('%s WaitForTurn %s for %s (depth=%d)', tag, ticket.label(), self.uuid, depth)
        while True:
            outcome = self.step(ticket, clock())
            if outcome == 'turn':
                _setCurrent(ticket)
                logging.debug('%s TurnReady %s for %s', tag, ticket.label(), self.uuid)
                return True
            if outcome != 'wait':
                logging.debug('%s Pas de diffusion pour %s (%s)', tag, ticket.label(), outcome)
                return False
            sleep(0.1)

    def _holdForce(self, ticket, tag, clock, sleep, cut):
        """ Tour d'un « force », sans attendre la file : abandon de la notification de la file qui n'a pas lancé sa diffusion, puis
        coupure de la diffusion en cours (cut), puis attente de la sortie des notifications qui l'avaient lancée (volume rétabli,
        application arrêtée), au plus queueForceCutWait secondes. Un autre « force » qui n'a pas lancé sa diffusion n'est pas attendu """
        with self.lock:
            if ticket.state == ORPHANED:
                logging.debug('%s Pas de diffusion pour %s (orphaned)', tag, ticket.label())
                return False
            holder = self._activeHolder()
            if holder is not None and holder.phase not in LAUNCHED_PHASES:
                holder.state = ORPHANED
                logging.info('%s Notification non diffusée : %s pour %s, une notification « force » passe devant.', tag, holder.label(), self.uuid)
                self._advance()
        if cut is not None:
            cut()
        deadline = clock() + self.config.queueForceCutWait
        while True:
            now = clock()
            with self.lock:
                if ticket.state == ORPHANED:
                    logging.debug('%s Pas de diffusion pour %s (orphaned)', tag, ticket.label())
                    return False
                launched = [t for t in self._launchedOccupants() if t is not ticket]
                if not launched:
                    break
                if now >= deadline:
                    for occupant in launched:
                        occupant.state = ORPHANED
                        logging.warning('%s Notification abandonnée : %s toujours en cours pour %s %ds après sa coupure par une notification « force ».',
                                        tag, occupant.label(), self.uuid, int(self.config.queueForceCutWait))
                    self._advance()
                    break
            sleep(0.1)
        _setCurrent(ticket)
        return True

    def step(self, ticket, now):
        """ Une vérification de l'attente : 'turn', 'wait', 'abandoned' ou 'orphaned' """
        with self.lock:
            if ticket.state == ORPHANED:
                return 'orphaned'
            if ticket.state == ABANDONED:
                return 'abandoned'
            if self._canTakeTurn(ticket):
                ticket.state = ACTIVE
                self._setPhase(ticket, 'tour', self.config.queuePrepTimeout, now)
                return 'turn'
            age = now - ticket.arrival
            if age >= self.config.queueMaxAge:
                ticket.state = ABANDONED
                logging.warning("[DAEMON][WaitQueue][%s] Notification abandonnée : %s en attente depuis %ds pour %s, au-delà de l'âge maximal. Elle n'est pas diffusée.",
                                ticket.callerName, ticket.label(), int(age), self.uuid)
                self._advance()
                return 'abandoned'
            for blocker in self._blockers():
                if blocker is not ticket and blocker.deadline is not None and now > blocker.deadline:
                    self._orphan(blocker, now)
            return 'wait'

    # ── Sortie (thread de la notification) ───────────────────────────────────

    def release(self, ticket):
        """ Fin de la notification (diffusée, en erreur ou non diffusée) : sans effet si déjà sortie ou orpheline """
        with self.lock:
            if ticket.state == ORPHANED:
                logging.debug('[DAEMON][WaitQueue][%s] Sortie de %s pour %s ignorée : déjà déclarée bloquée', ticket.callerName, ticket.label(), self.uuid)
            elif ticket.state not in FINISHED:
                ticket.state = DONE
                logging.debug('[DAEMON][WaitQueue][%s] Out %s for %s', ticket.callerName, ticket.label(), self.uuid)
            self._advance()
        if current() is ticket:
            _setCurrent(None)

    # ── Interne (sous self.lock) ─────────────────────────────────────────────

    def _setPhase(self, ticket, name, seconds, now):
        ticket.phase = name
        ticket.lastActivity = now
        ticket.deadline = now + seconds + self.config.queueStallMargin

    def _canTakeTurn(self, ticket):
        if any(f.state not in FINISHED for f in self.forces):
            return False
        if ticket.kind == 'auto':
            return self.serving == ticket.number
        block = ticket.block
        return self.serving == block.number and block.activeMember() is None and block.nextMember() is ticket

    def _activeHolder(self):
        """ Notification de la file (hors « force ») qui occupe l'équipement, ou None """
        unit = self.units.get(self.serving)
        holder = unit.activeMember() if isinstance(unit, Block) else unit
        return holder if holder is not None and holder.state == ACTIVE else None

    def _launchedOccupants(self):
        """ Notifications (de la file ou « force ») qui ont lancé leur diffusion et n'en sont pas sorties """
        candidates = [self._activeHolder()] + [f for f in self.forces if f.state == ACTIVE]
        return [t for t in candidates if t is not None and t.phase in LAUNCHED_PHASES]

    def _blockers(self):
        """ Notifications qui occupent l'équipement ou dont la suite de la file attend la préparation """
        blockers = [f for f in self.forces if f.state not in FINISHED]
        unit = self.units.get(self.serving)
        if isinstance(unit, Ticket):
            holder = unit
        elif isinstance(unit, Block):
            holder = unit.activeMember() or unit.nextMember()
        else:
            holder = None
        if holder is not None and holder.state in (PREPARING, ACTIVE):
            blockers.append(holder)
        return blockers

    def _orphan(self, ticket, now):
        ticket.state = ORPHANED
        logging.warning('[DAEMON][WaitQueue][%s] Notification bloquée : %s sans progression depuis %ds (étape : %s) pour %s. Elle est abandonnée et la suivante est diffusée.',
                        ticket.callerName, ticket.label(), int(now - ticket.lastActivity), ticket.phase, self.uuid)
        self._advance()

    def _advance(self):
        while self.serving < self.tail:
            unit = self.units.get(self.serving)
            if unit is not None and not (unit.finished() if isinstance(unit, Block) else unit.state in FINISHED):
                break
            if isinstance(unit, Block) and self.blocksByPid.get(unit.pid) == unit.number:
                self.blocksByPid.pop(unit.pid, None)
            self.units.pop(self.serving, None)
            self.serving += 1
        self.forces = [f for f in self.forces if f.state not in FINISHED]
