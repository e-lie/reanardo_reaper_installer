import time

from ..TimeVar import TimeVar

def get_bpm(self):
    """ Returns the current beats per minute as a floating point number """
    if isinstance(self.bpm, TimeVar):
        bpm_val = self.bpm.now(self.beat_count)
    else:
        bpm_val = self.bpm
    return float(bpm_val)

def get_latency(self):
    """ Returns self.latency (which is in seconds) as a fraction of a beat """
    return self.seconds_to_beats(self.latency)

def get_elapsed_beats_from_last_bpm_change(self):
    """ Returns the number of beats that *should* have elapsed since the last tempo change """
    return float(
        self.get_elapsed_seconds_from_last_bpm_change() *
        (self.get_bpm() / 60)
    )

def get_elapsed_seconds_from_last_bpm_change(self):
    """ Returns the time since the last change in bpm """
    return self.get_time() - self.bpm_start_time

def get_time(self):
    """ Returns current machine clock time with nudges values added """
    return time.time() + float(self.nudge) + float(self.hard_nudge)

def get_time_at_beat(self, beat):
    """ Returns the time that the local computer's clock will be at 'beat' value """
    if isinstance(self.bpm, TimeVar):
        t = self.get_time() + self.beat_dur(beat - self.now())
    else:
        t = self.bpm_start_time + self.beat_dur(beat - self.bpm_start_beat)
    return t

def bar_length(self):
    """ Returns the length of a bar in terms of beats """
    return (float(self.meter[0]) / self.meter[1]) * 4

def bars(self, n=1):
    """ Returns the number of beats in 'n' bars """
    return self.bar_length() * n

def beat_dur(self, n=1):
    """ Returns the length of n beats in seconds """

    return 0 if n == 0 else (60.0 / self.get_bpm()) * n

def beats_to_seconds(self, beats):
    return self.beat_dur(beats)

def seconds_to_beats(self, seconds):
    """ Returns the number of beats that occur in a time period  """
    return (self.get_bpm() / 60.0) * seconds

