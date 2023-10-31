"""
    Clock management for scheduling notes and functions. Anything 'callable', such as a function
    or instance with a `__call__` method, can be scheduled. An instance of `TempoClock` is created
    when FoxDot started up called `Clock`, which is used by `Player` instances to schedule musical
    events. 

    The `TempoClock` is also responsible for sending the osc messages to SuperCollider. It contains
    a queue of event blocks, instances of the `QueueBlock` class, which themselves contain queue
    items, instances of the `QueueObj` class, which themseles contain the actual object or function
    to be called. The `TempoClock` is continually running and checks if any queue block should 
    be activated. A queue block has a "beat" value for which its contents should be activated. To make
    sure that events happen on time, the `TempoClock` will begin processing the contents 0.25
    seconds before it is *actually* meant to happen in case there is a large amount to process.  When 
    a queue block is activated, a new thread is created to process all of the callable objects it
    contains. If it calls a `Player` object, the queue block keeps track of the OSC messages generated 
    until all `Player` objects in the block have been called. At this point the thread is told to
    sleep until the remainder of the 0.25 seconds has passed. This value is stored in `Clock.latency`
    and is adjustable. If you find that there is a noticeable jitter between events, i.e. irregular
    beat lengths, you can increase the latency by simply evaluating the following in FoxDot:

        Clock.latency = 0.5

    To stop the clock from scheduling further events, use the `Clock.clear()` method, which is
    bound to the shortcut key, `Ctrl+.`. You can schedule non-player objects in the clock by
    using `Clock.schedule(func, beat_count, args, kwargs)`. By default `beat` is set to the next
    bar in the clock, but you use `Clock.now() + n` or `Clock.next_bar() + n` to schedule a function
    in the future at a specific time. 

    To change the tempo of the clock, just set the bpm attribute using `Clock.bpm=val`. The change
    in tempo will occur at the start of the next bar so be careful if you schedule this action within
    a function like this:

        def myFunc():
            print("bpm change!")
            Clock.bpm+=50

    This will print the string `"bpm change"` at the next bar and change the bpm value at the
    start of the *following* bar. The reason for this is to make it easier for calculating
    currently clock times when using a `TimeVar` instance (See docs on TimeVar.py) as a tempo.

    You can change the clock's time signature as you would change the tempo by setting the
    `meter` attribute to a tuple with two values. So for 3/4 time you would use the follwing
    code:

        Clock.meter = (3,4)

"""

from __future__ import absolute_import, division, print_function


from ..Players import Player
from ..TimeVar import TimeVar
from ..ServerManager import ServerManager
from .EventQueue import Queue, History, Wrapper
from .SoloPlayer import SoloPlayer

import time
from traceback import format_exc as error_stack

import sys
import threading


class ScheduleError(Exception):
    def __init__(self, item):
        self.type = str(type(item))[1:-1]

    def __str__(self):
        return "Could not schedule object of {}".format(self.type)


class TempoClock(object):

    tempo_server = None

    def __init__(self, bpm=120.0, meter=(4, 4)):

        # Flag this when done init
        self.__setup = False

        # debug information
        self.largest_sleep_time = 0
        self.last_block_dur = 0.0

        self.beat_count = 0.0  # Beats elapsed
        self.ticking = True

        self.last_now_call = 0.0

        # Player Objects stored here
        self.playing = []

        # Store history of osc messages and functions in here
        self.history = History()

        # All other scheduled items go here
        self.items = []

        # General set up
        self.bpm = bpm
        self.meter = meter

        # Create the queue
        self.queue = Queue(clock=self)
        self.current_block = None

        # Flag for next_bar wrapper
        self.now_flag = False

        # Can be configured
        self.latency = 0.25  # Time between starting processing osc messages and sending to server

        self.nudge = 0.0  # If you want to synchronise with something external, adjust the nudge
        self.hard_nudge = 0.0

        self.bpm_start_time = time.time()
        self.bpm_start_beat = 0

        # The duration to sleep while continually looping
        self.sleep_time = 0.0001
        self.midi_nudge = 0

        # Debug
        self.debugging = False
        self.__setup = True

        # If one object is going to be played
        self.solo = SoloPlayer()
        self.thread = threading.Thread(target=self.run)
    

    def __setattr__(self, attr, value):
        if attr == "bpm" and self.__setup:
            # Schedule for next bar
            start_beat, start_time = self.update_bpm(value)
        elif attr == "midi_nudge" and self.__setup:
            # Adjust nudge for midi devices
            self.server.set_midi_nudge(value)
            object.__setattr__(self, "midi_nudge", value)
        else:
            self.__dict__[attr] = value
        return

    def __str__(self):
        return str(self.queue)

    def __iter__(self):
        for x in self.queue:
            yield x

    def __len__(self):
        return len(self.queue)

    def __contains__(self, item):
        return item in self.items

    from ._time_beat_getters import (seconds_to_beats, beats_to_seconds, beat_dur,
                                     bar_length, bars,
                                     get_elapsed_beats_from_last_bpm_change,
                                     get_elapsed_seconds_from_last_bpm_change,
                                     get_time, get_bpm,
                                     get_time_at_beat, get_latency)
    from ._utility_methods import swing, every, shift
    # from ._a import *

    def start_thread(self):
        """ Starts the clock thread """
        self.thread.daemon = True
        self.thread.start()
        return

    def stop(self):
        self.ticking = False
        self.clear()
        return

    def run(self):
        """ Main loop """
        self.ticking = True
        self.polled = False
        while self.ticking:
            self.update_beat_count()  # get current time
            if self.queue.after_next_event(self.beat_count):
                self.current_block = self.queue.pop()
                # Do the work in a thread
                if len(self.current_block):
                    threading.Thread(
                        target=self.__run_block,
                        args=(self.current_block, self.beat_count)
                    ).start()
            if self.sleep_time > 0:
                time.sleep(self.sleep_time)
        return

    @classmethod
    def set_server(cls, server):
        """ Sets the destination for OSC messages being compiled (the server is also the class
            that compiles them) via objects in the clock. Should be an instance of ServerManager -
            see ServerManager.py for more. """
        assert isinstance(server, ServerManager)
        cls.server = server
        return

    def update_bpm(self, bpm):
        """ Schedules the bpm change at the next bar, returns the beat and start time of the next change """
        try:
            assert bpm > 0, "Tempo must be a positive number"
        except AssertionError as err:
            raise (ValueError(err))

        next_bar = self.next_bar()
        bpm_start_time = self.get_time_at_beat(next_bar)
        bpm_start_beat = next_bar

        def func():
            object.__setattr__(self, "bpm", bpm)
            self.last_now_call = self.bpm_start_time = bpm_start_time
            self.bpm_start_beat = bpm_start_beat
        # Give next bar value to bpm_start_beat
        self.schedule(func, next_bar, is_priority=True)
        return bpm_start_beat, bpm_start_time

 
    # def set_time(self, beat):
    #     """ Set the clock time to 'beat' and update players in the clock """
    #     self.start_time = time.time()
    #     self.queue.clear()
    #     self.beat_count = beat
    #     self.bpm_start_beat = beat
    #     self.bpm_start_time = self.start_time
    #     # self.time = time() - self.start_time
    #     for player in self.playing:
    #         player(count=True)


    def calculate_nudge(self, time1, time2, latency):
        """ Approximates the nudge value of this TempoClock based on the machine time.time()
            value from another machine and the latency between them """
        # self.hard_nudge = time2 - (time1 + latency)
        self.hard_nudge = time1 - time2 - latency

    def update_beat_count(self):
        """ If the bpm is an int or float, use time since the last bpm change to calculate what the current beat is. 
            If the bpm is a TimeVar, increase the beat counter by time since last call to update_beat_count()"""
        if isinstance(self.bpm, (int, float)):
            self.beat_count = self.bpm_start_beat + self.get_elapsed_beats_from_last_bpm_change()
        else:
            now = self.get_time()
            self.beat_count += (now - self.last_now_call) * (self.get_bpm() / 60)
            self.last_now_call = now

    def now(self):
        """ Returns the total elapsed time (in beats as opposed to seconds) """
        if self.ticking is False:  # Get the time without latency if not ticking
            self.update_beat_count()
        return float(self.beat_count)

    def mod(self, beat, t=0):
        """ Returns the next time at which `Clock.now() % beat` will equal `t` """
        n = self.now() // beat
        return (n + 1) * beat + t

    def osc_message_time(self):
        """ Returns the true time that an osc message should be run i.e. now + latency """
        return time.time() + self.latency

    def _adjust_hard_nudge(self):
        """ Checks for any drift between the current beat value and the value
            expected based on time elapsed and adjusts the hard_nudge value accordingly """
        beats_elapsed = int(self.now()) - self.bpm_start_beat
        expected_beat = self.get_elapsed_beats_from_last_bpm_change()
        # Dont adjust nudge on first bar of tempo change
        if beats_elapsed > 0:
            # Account for nudge in the drift
            self.drift = self.beat_dur(expected_beat - beats_elapsed) - self.nudge
            # value could be reworked / not hard coded
            if abs(self.drift) > 0.001:
                self.hard_nudge -= self.drift
        return self._schedule_adjust_hard_nudge()

    def _schedule_adjust_hard_nudge(self):
        """ Start recursive call to adjust hard-nudge values """
        return self.schedule(self._adjust_hard_nudge)

    def __run_block(self, block, beat_count):
        """ Private method for calling all the items in the queue block.
            This means the clock can still 'tick' while a large number of
            events are activated  """
        # Set the time to "activate" messages on - adjust in case the block is activated late
        # `beat` is the actual beat this is happening, `block.beat` is the desired time. Adjust
        # the osc_message_time accordingly if this is being called late
        block.time = self.osc_message_time(
        ) - self.beat_dur(float(beat_count) - block.beat_count)
        for item in block:
            # The item might get called by another item in the queue block
            output = None
            if item.called is False:
                try:
                    output = item.__call__()
                except SystemExit:
                    sys.exit()
                except:
                    print(error_stack())
                # TODO: Get OSC message from the call, and add to list?
        # Send all the message to supercollider together
        block.send_osc_messages()
        # Store the osc messages -- future idea
        # self.history.add(block.beat_count, block.osc_messages)


    def schedule(self, obj, beat_count=None, args=(), kwargs={}, is_priority=False):
        """ TempoClock.schedule(callable, beat_count=None)
            Add a player / event to the queue """
        # Make sure the object can actually be called
        try:
            assert callable(obj)
        except AssertionError:
            raise ScheduleError(obj)
        # Start the clock ticking if not already
        if self.ticking == False:
            self.start_thread()
        # Default is next bar
        if beat_count is None:
            beat_count = self.next_bar()
        # Keep track of objects in the Clock
        if obj not in self.playing and isinstance(obj, Player):
            self.playing.append(obj)
        if obj not in self.items:
            self.items.append(obj)
        # Add to the queue
        self.queue.add(obj, beat_count, args, kwargs, is_priority)
        # block.time = self.osc_message_accum


    def future(self, dur, obj, args=(), kwargs={}):
        """ Add a player / event to the queue `dur` beats in the future """
        self.schedule(obj, self.now() + dur, args, kwargs)


    def next_bar(self):
        """ Returns the beat value for the start of the next bar """
        beat_count = self.now()
        return beat_count + (self.meter[0] - (beat_count % self.meter[0]))

    def next_event(self):
        """ Returns the beat index for the next event to be called """
        return self.queue[-1][1]

    def call(self, obj, dur, args=()):
        """ Returns a 'schedulable' wrapper for any callable object """
        return Wrapper(self, obj, dur, args)

    def players(self, ex=[]):
        return [p for p in self.playing if p not in ex]

    def clear(self):
        """ Remove players from clock """
        self.items = []
        self.queue.clear()
        self.solo.reset()
        for player in list(self.playing):
            player.kill()
        # for item in self.items:
        #     if hasattr(item, 'stop'):
        #         item.stop()
        self.playing = []
