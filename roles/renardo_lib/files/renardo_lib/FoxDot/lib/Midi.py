""" Module for converting handling MIDI in/out and functions relating to MIDI pitch calculation. """

from __future__ import absolute_import, division, print_function

try:
    import rtmidi
    from rtmidi import midiconstants
    TIMING_CLOCK = midiconstants.TIMING_CLOCK
    SONG_POSITION_POINTER = midiconstants.SONG_POSITION_POINTER
    SONG_START = midiconstants.SONG_START
    SONG_STOP = midiconstants.SONG_STOP
except ImportError as _err:
    pass

from .Patterns import asStream
from .Scale import ScalePattern
from .TimeVar import TimeVar
from .SCLang import SynthDefProxy

import time


class MidiInputHandler(object):

    """Midi Handler CallBack Function"""

    def __init__(self, midi_ctrl):

        self.midi_ctrl = midi_ctrl
        self.bpm_group = []
        self.played = False
        self.bpm = 120.0
        self.tt = False
        self.tt_bpm = self.bpm
        self.tt_time = time.time()
        self.tt_ptime = self.tt_time
        self.msg = [0, 0, 0]
        self.n_msg_list = []
        self.c_msg_list = []
        self.print_msg = False

    def __call__(self, event, data=None):

        message, delta = event

        self.msg = message

        if self.print_msg == True:
            print(self.msg)

        if(self.msg[0] == 144 or self.msg[0] == 145):
            if len(self.n_msg_list) == 0:
                self.n_msg_list.append(self.msg)
            else:
                if self.msg not in self.n_msg_list:
                    self.n_msg_list.append(self.msg)
        elif self.msg[0] == 128 or self.msg[0] == 129:
            if len(self.n_msg_list) > 0:
                for count, item in enumerate(self.n_msg_list):
                    if self.msg[1] == item[1]:
                        self.n_msg_list.remove(self.n_msg_list[count])
        else:
            if len(self.c_msg_list) == 0:
                self.c_msg_list.append(self.msg)
            elif self.msg not in self.c_msg_list:
                self.c_msg_list.append(self.msg)
            for count, item in enumerate(self.c_msg_list):
                if self.msg[0] == item[0] and self.msg[1] == item[1] and self.msg[2] != item[2]:
                    self.c_msg_list.remove(self.c_msg_list[count])
                elif self.msg[0] == item[0] and self.msg[1] == item[1]:
                    self.c_msg_list[count] = self.msg

        if self.tt and message[0] == 128 and message[1] == 0:
            self.tt_time = time.time()
            if self.tt_ptime < self.tt_time:
                self.tt_bpm = (1/(self.tt_time - self.tt_ptime)) * 60
                self.tt_ptime = self.tt_time
        #
        self.midi_ctrl.delta += delta
        #if TIMING_CLOCK in datatype and not self.played:
        if not self.played:
            self.midi_ctrl.pulse += 1
            if self.midi_ctrl.pulse == self.midi_ctrl.ppqn:
                t_master = 60.0
                self.midi_ctrl.bpm = round(60.0 / self.midi_ctrl.delta, 0)
                self.midi_ctrl.pulse = 0
                self.midi_ctrl.delta = 0.0
                #print("CONTROLLER BPM : " + repr(self.midi_ctrl.bpm))


class MidiIn:
    metro = None

    def __init__(self, port_id=0):
        """ Class for listening for MIDI clock messages
            from a midi device """
        try:
            self.device = rtmidi.MidiIn()
        except NameError:
            raise ImportError(_err)

        self.available_ports = self.device.get_ports()

        if not self.available_ports:
            raise MIDIDeviceNotFound
        else:
            print("MidiIn: Connecting to " + self.available_ports[port_id])

        self.device.open_port(port_id)
        self.device.ignore_types(timing=False)

        self.pulse = 0
        self.delta = 0.0
        self.bpm = 120.0
        self.tt_bpm = 120.0
        self.ppqn = 24
        self.beat = 0
        self.ctrl_value = 0
        self.note = 0
        self.velocity = 0
        self.handler = MidiInputHandler(self)
        self.device.set_callback(self.handler)
        self.msg = self.handler.msg

    @classmethod
    def set_clock(cls, tempo_clock):
        cls.metro = tempo_clock
        return

    def tempo_tapper(self, tt_bool):
        """ Activate Tempo Tapper Device """
        self.handler.tt = tt_bool
        return

    def tempo_tapper_bpm(self):
        """ Get Beats per Minute (bpm) value """
        self.bpm = self.handler.tt_bpm
        return self.bpm

    def get_ctrl(self, channel):
        """ Get control value from knobs / pads """
        for i in range(len(self.handler.c_msg_list)):
            if self.handler.c_msg_list[i][1] == channel:
                self.ctrl_value = self.handler.c_msg_list[i][2]
        return self.ctrl_value

    def get_note(self):
        """ Get midinote from keys"""
        self.note = ()
        if len(self.handler.n_msg_list) > 0:
            for i in range(len(self.handler.n_msg_list)):
                self.note = self.note + (self.handler.n_msg_list[i][1], )
        else:
            self.note = self.note + (0, )
        return self.note

    def get_velocity(self):
        """ Get velocity of midi keys / pads """
        self.velocity = ()
        if len(self.handler.n_msg_list) > 0:
            for i in range(len(self.handler.n_msg_list)):
                self.velocity = self.velocity + \
                    (self.handler.n_msg_list[i][2] / 64, )
        else:
            self.velocity = (0, )
        return self.velocity

    def get_delta(self):
        """ Get delta """
        self.delta = self.handler.delta
        return self.delta

    def print_message(self, boolmsg):
        """ Print incoming midi message"""
        self.handler.print_msg = boolmsg
        return self.handler.print_msg

    def close(self):
        """ Closes the active port """
        self.device.close_port()
        return


class MidiOut(SynthDefProxy):
    """ SynthDef proxy for sending midi message via supercollider """

    def __init__(self, degree=0, **kwargs):
        SynthDefProxy.__init__(self, self.__class__.__name__, degree, kwargs)


class ReaperInstrument(MidiOut):
    """SynthDef proxy to handle MIDI + PyLive/LiveOSC integration"""
    def __init__(self, degree=0, **kwargs):
        if isinstance(degree, str) and "midi_map" not in kwargs.keys():
            raise Exception("No midi map defined to translate playstring")
        MidiOut.__init__(self, degree, **kwargs)

# midi = MidiOut  # experimental alias
# Midi information exceptions


class MIDIDeviceNotFound(Exception):
    def __str__(self):
        return self.__class__.__name__ + " Error"


class rtMidiNotFound(Exception):
    def __str__(self):
        return self.__class__.__name__ + ": Module 'rtmidi' not found"


if __name__ == "__main__":
    a = MidiIn()
