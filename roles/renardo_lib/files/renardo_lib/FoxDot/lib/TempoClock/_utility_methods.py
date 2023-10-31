from ..TimeVar import TimeVar

def swing(self, amount=0.1):
    """ Sets the nudge attribute to var([0, amount * (self.bpm / 120)],1/2)"""
    self.nudge = TimeVar(
        [0, amount * (self.bpm / 120)], 1 / 2
    ) if amount != 0 else 0
    return

# Every n beats, do...
def every(self, n, cmd, args=()):
    def event(f, n, args):
        f(*args)
        self.schedule(event, self.now() + n, (f, n, args))
        return
    self.schedule(event, self.now() + n, args=(cmd, n, args))
    return

def shift(self, n):
    """ Offset the clock time """
    self.beat_count += n
    return