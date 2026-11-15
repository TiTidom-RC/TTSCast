""" File d'attente des notifications (waitqueue) : ordre, blocs « wait », « force », âge maximal, notifications bloquées, sorties.
Horloge simulée : chaque vérification d'attente est faite par step(ticket, now), sans thread ni attente réelle.
Lancement depuis resources/ttscastd :  python -m unittest discover -s tests -t . """

import types as pytypes
import unittest

import waitqueue
from waitqueue import ABANDONED, ACTIVE, DONE, ORPHANED

CONFIG = pytypes.SimpleNamespace(queueMaxAge=600, queueStallMargin=15, queuePrepTimeout=30)


class QueueTestCase(unittest.TestCase):
    def setUp(self):
        self.q = waitqueue.DeviceQueue('enceinte-test', CONFIG)
        self.now = 0.0
        self.addCleanup(waitqueue._setCurrent, None)

    def auto(self, name='TTS'):
        return self.q.register('auto', name, self.now)

    def wait(self, value, pid=1000):
        return self.q.register('wait', 'TTS', self.now, waitValue=value, pid=pid)

    def ready(self, *tickets):
        for t in tickets:
            t.state = waitqueue.READY

    def step(self, ticket):
        return self.q.step(ticket, self.now)


class OrderTest(QueueTestCase):
    def test_fifo(self):
        a, b, c = self.auto(), self.auto(), self.auto()
        self.ready(a, b, c)
        self.assertEqual(self.step(b), 'wait')
        self.assertEqual(self.step(a), 'turn')
        self.assertEqual(self.step(c), 'wait')
        self.q.release(a)
        self.assertEqual(self.step(c), 'wait')
        self.assertEqual(self.step(b), 'turn')
        self.q.release(b)
        self.assertEqual(self.step(c), 'turn')

    def test_releasedBeforeTurnIsSkipped(self):
        """ Notification sortie avant son tour (option refusée, erreur de génération) : la file passe à la suivante """
        a, b, c = self.auto(), self.auto(), self.auto()
        self.ready(a, c)
        self.assertEqual(self.step(a), 'turn')
        self.q.release(b)
        self.q.release(a)
        self.assertEqual(self.q.serving, 2)
        self.assertEqual(self.step(c), 'turn')

    def test_releaseIsIdempotent(self):
        a, b = self.auto(), self.auto()
        self.ready(a, b)
        self.step(a)
        self.q.release(a)
        self.q.release(a)
        self.assertEqual(self.q.serving, 1)
        self.assertEqual(self.step(b), 'turn')

    def test_isActive(self):
        self.assertFalse(self.q.isActive())
        a = self.auto()
        self.assertTrue(self.q.isActive())
        self.q.release(a)
        self.assertFalse(self.q.isActive())
        f = self.q.register('force', 'TTS', self.now)
        self.assertTrue(self.q.isActive())
        self.q.release(f)
        self.assertFalse(self.q.isActive())


class BlockTest(QueueTestCase):
    def test_orderByWaitValue(self):
        """ wait:2 puis wait:1 puis wait:3 (arrivée désordonnée) : un seul bloc, diffusé 1, 2, 3 ; la notification suivante après le bloc """
        w2, w1, w3 = self.wait(2), self.wait(1), self.wait(3)
        after = self.auto()
        self.assertEqual({w1.number, w2.number, w3.number}, {0})
        self.assertEqual(after.number, 1)
        self.ready(w1, w2, w3, after)
        self.assertEqual(self.step(w2), 'wait')
        self.assertEqual(self.step(w3), 'wait')
        self.assertEqual(self.step(w1), 'turn')
        self.assertEqual(self.step(w2), 'wait')
        self.q.release(w1)
        self.assertEqual(self.step(w3), 'wait')
        self.assertEqual(self.step(w2), 'turn')
        self.q.release(w2)
        self.assertEqual(self.step(after), 'wait')
        self.assertEqual(self.step(w3), 'turn')
        self.q.release(w3)
        self.assertEqual(self.step(after), 'turn')

    def test_sameWaitValueOneAfterTheOther(self):
        first, second = self.wait(1), self.wait(1)
        self.assertEqual((first.label(), second.label()), ('ticket 0 (wait=1 #1)', 'ticket 0 (wait=1 #2)'))
        self.ready(first, second)
        self.assertEqual(self.step(second), 'wait')
        self.assertEqual(self.step(first), 'turn')
        self.assertEqual(self.step(second), 'wait')
        self.q.release(first)
        self.assertEqual(self.step(second), 'turn')

    def test_lowerValueArrivingLateWaitsForActiveMember(self):
        w2 = self.wait(2)
        self.ready(w2)
        self.assertEqual(self.step(w2), 'turn')
        w1 = self.wait(1)
        self.ready(w1)
        self.assertEqual(self.step(w1), 'wait')
        self.q.release(w2)
        self.assertEqual(self.step(w1), 'turn')

    def test_twoPidsTwoBlocks(self):
        a1, b1 = self.wait(1, pid=1), self.wait(1, pid=2)
        self.assertEqual((a1.number, b1.number), (0, 1))
        self.ready(a1, b1)
        self.assertEqual(self.step(b1), 'wait')
        self.assertEqual(self.step(a1), 'turn')

    def test_lateMemberAfterBlockEndOpensNewBlock(self):
        w1 = self.wait(1)
        self.ready(w1)
        self.step(w1)
        self.q.release(w1)
        late = self.wait(2)
        self.assertEqual(late.number, 1)
        self.ready(late)
        self.assertEqual(self.step(late), 'turn')


class ForceTest(QueueTestCase):
    def test_forceFreezesQueue(self):
        a, b = self.auto(), self.auto()
        self.ready(a, b)
        self.step(a)
        force = self.q.register('force', 'TTS', self.now)
        self.assertEqual(force.state, ACTIVE)
        self.q.release(a)  # coupée par le force
        self.assertEqual(self.step(b), 'wait')
        self.q.release(force)
        self.assertEqual(self.step(b), 'turn')

    def test_overlappingForces(self):
        a = self.auto()
        self.ready(a)
        f1 = self.q.register('force', 'TTS', self.now)
        f2 = self.q.register('force', 'TTS', self.now)
        self.q.release(f1)
        self.assertEqual(self.step(a), 'wait')
        self.q.release(f2)
        self.assertEqual(self.step(a), 'turn')

    def test_stuckForceIsOrphaned(self):
        a = self.auto()
        self.ready(a)
        force = self.q.register('force', 'TTS', self.now)
        force.setPhase('lecture', 20, self.now)
        self.now = 20 + CONFIG.queueStallMargin + 1
        self.assertEqual(self.step(a), 'wait')
        self.assertEqual(force.state, ORPHANED)
        self.assertEqual(self.step(a), 'turn')


class StallTest(QueueTestCase):
    def test_progressingNotificationNeverOrphaned(self):
        """ Notification active de 5 minutes qui progresse : ni elle ni la suivante ne sont abandonnées """
        a, b = self.auto(), self.auto()
        self.ready(a, b)
        self.step(a)
        a.setPhase('lecture', 20, self.now)
        for _ in range(60):
            self.now += 5
            a.progress(20, self.now)
            self.assertEqual(self.step(b), 'wait')
        self.assertEqual(a.state, ACTIVE)
        self.q.release(a)
        self.assertEqual(self.step(b), 'turn')

    def test_stuckActiveIsOrphanedAndNextPlays(self):
        a, b = self.auto(), self.auto()
        self.ready(a, b)
        self.step(a)
        a.setPhase('lecture', 20, self.now)
        self.now = 20 + CONFIG.queueStallMargin - 1
        self.assertEqual(self.step(b), 'wait')
        self.assertEqual(a.state, ACTIVE)
        self.now += 2
        self.assertEqual(self.step(b), 'wait')
        self.assertEqual(a.state, ORPHANED)
        self.assertEqual(self.step(b), 'turn')
        self.q.release(a)  # réveil tardif : sans effet
        self.assertEqual(self.q.serving, 1)
        self.q.release(b)
        self.assertEqual(self.q.serving, 2)

    def test_stuckPreparationAtHeadIsOrphaned(self):
        """ Notification dont c'est le tour mais encore en préparation (reformulation IA bloquée) """
        a, b = self.auto(), self.auto()
        a.setPhase('reformulation IA', 60, self.now)
        self.ready(b)
        self.now = 60 + CONFIG.queueStallMargin + 1
        self.assertEqual(self.step(b), 'wait')
        self.assertEqual(a.state, ORPHANED)
        self.assertEqual(self.step(b), 'turn')
        self.assertFalse(self.q.hold(a, clock=lambda: self.now, sleep=lambda s: None))

    def test_readyTicketAtHeadIsNotOrphaned(self):
        """ Notification prête dont c'est le tour, ancienne échéance de préparation dépassée : elle prend son tour, pas d'abandon """
        a, b = self.auto(), self.auto()
        self.ready(a, b)
        self.now = 500
        self.assertEqual(self.step(b), 'wait')
        self.assertEqual(self.step(a), 'turn')

    def test_stuckBlockMember(self):
        w1, w2 = self.wait(1), self.wait(2)
        self.ready(w1, w2)
        self.step(w1)
        w1.setPhase('lecture', 20, self.now)
        self.now = 40
        self.assertEqual(self.step(w2), 'wait')
        self.assertEqual(w1.state, ORPHANED)
        self.assertEqual(self.step(w2), 'turn')


class AgeTest(QueueTestCase):
    def test_tooOldIsAbandonedAndSkipped(self):
        a, b, c = self.auto(), self.auto(), self.auto()
        self.ready(a, b)
        self.step(a)
        self.now = CONFIG.queueMaxAge - 1
        a.progress(20, self.now)
        self.assertEqual(self.step(b), 'wait')
        self.now = CONFIG.queueMaxAge
        a.progress(20, self.now)
        self.assertEqual(self.step(b), 'abandoned')
        self.assertEqual(b.state, ABANDONED)
        self.ready(c)
        self.q.release(a)
        self.assertEqual(self.q.serving, 2)
        self.assertEqual(self.step(c), 'turn')

    def test_blockAgeFromFirstMember(self):
        a = self.auto()
        self.ready(a)
        self.step(a)
        w1 = self.wait(1)
        self.now = 300
        w2 = self.wait(2)
        self.ready(w1, w2)
        self.now = CONFIG.queueMaxAge
        a.progress(20, self.now)
        self.assertEqual(self.step(w2), 'abandoned')


class HoldAndHelpersTest(QueueTestCase):
    def test_holdSetsCurrentAndReleaseClearsIt(self):
        a = self.auto()
        self.assertTrue(self.q.hold(a, clock=lambda: self.now, sleep=lambda s: None))
        self.assertIs(waitqueue.current(), a)
        waitqueue.phase('génération', 30, self.now)
        self.assertEqual((a.phase, a.deadline), ('génération', 30 + CONFIG.queueStallMargin))
        waitqueue.progress(20, 10)
        self.assertEqual((a.phase, a.deadline), ('génération', 10 + 20 + CONFIG.queueStallMargin))
        self.assertFalse(waitqueue.isOrphaned())
        a.state = ORPHANED
        self.assertTrue(waitqueue.isOrphaned())
        self.q.release(a)
        self.assertIsNone(waitqueue.current())

    def test_holdWaitsThenTakesTurn(self):
        a, b = self.auto(), self.auto()
        self.q.hold(a, clock=lambda: self.now, sleep=lambda s: None)

        def sleep(_seconds):
            self.now += 0.1
            if self.now >= 3:
                self.q.release(a)
        self.assertTrue(self.q.hold(b, clock=lambda: self.now, sleep=sleep))
        self.assertGreaterEqual(self.now, 3)
        self.assertEqual(b.state, ACTIVE)

    def test_forceHoldIsImmediate(self):
        a = self.auto()
        self.ready(a)
        self.step(a)
        force = self.q.register('force', 'TTS', self.now)
        self.assertTrue(self.q.hold(force, clock=lambda: self.now, sleep=lambda s: self.fail('force ne doit pas attendre')))
        self.assertIs(waitqueue.current(), force)

    def test_helpersWithoutQueue(self):
        waitqueue.phase('lecture', 20)
        waitqueue.progress(20)
        self.assertFalse(waitqueue.isOrphaned())
        self.assertIsNone(waitqueue.current())

    def test_finishedTicketIgnoresPhase(self):
        a = self.auto()
        self.q.release(a)
        a.setPhase('lecture', 20, self.now)
        self.assertEqual(a.state, DONE)
        self.assertEqual(a.phase, 'préparation')


if __name__ == '__main__':
    unittest.main()
