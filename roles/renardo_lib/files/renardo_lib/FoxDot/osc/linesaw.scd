SynthDef.new(\linesaw, {
	|bus = 0, freq = 1000, pan = 0, amp = 0.1, fmod=0, atk = 0.001, sus = 1, rel = 1.3, crv = -2,
	lforate1 = 5, lfodepth1 = 0.25, phasecenter1 = 0.35,
	lforate2 = 2.7, lfodepth2 = 0.5, phasecenter2 = 0.5,
	pswitch = 0, fdelay1 = 0.00025, fdelay2 = 0.00015|
	var input, lfoA, lfoB, phaseShiftA, phaseShiftB, env, saw,
	polarity, phaseA, phaseB, phase, osc;
	freq = In.kr(bus, 1);
	freq = [freq, freq+fmod];
	input = Line.ar(start: 0, end: atk + sus + rel, dur: atk + sus + rel, doneAction: 0);
	input = input - [0, fdelay1, fdelay2];
	lfoA = sin(2pi * (lforate1 * input).mod(1)) * lfodepth1;
	lfoB = sin(2pi * (lforate2 * input).mod(1)) * lfodepth2;
	phaseShiftA = (phasecenter1 + lfoA).wrap(0, 1);
	phaseShiftB = (phasecenter2 + lfoB).wrap(0, 1);
	env = (input/atk).clip(0, 1);
	env = env - ((input - (atk + sus))/rel).clip(0, 1);
	env = env.pow(exp(-1 * crv));
	saw = (input * freq).mod(1);
	polarity = 1 - (2 * pswitch);
	phaseA = sign(sign(phaseShiftA - saw) + 0.5);
	phaseA = (phaseA - 1)/2 - phaseShiftA + 0.5;
	phaseA = saw + phaseA;
	phaseB = sign(sign(phaseShiftB - saw) + 0.5);
	phaseB = (phaseB - 1)/2 - phaseShiftB + 0.5;
	phaseB = saw + phaseB;
	osc = ((polarity * (saw - 0.5)) + phaseA + phaseB)/2;
	osc = (osc[0] + osc[1] + osc[2])/3 * amp;
	osc = osc.softclip;
	osc = [osc * cos((pan + 1) * pi/4), osc * sin((pan + 1) * pi/4)];
	osc = osc * env * amp * 0.4;
	osc = Pan2.ar(osc, pan);
	ReplaceOut.ar(bus, osc)
},
metadata: (
	credit: "by Josh Mitchell",
	modified_by: "Jens Meisner",
	description: "",
	category: \pads,
	tags: [\pitched]
)
).add;