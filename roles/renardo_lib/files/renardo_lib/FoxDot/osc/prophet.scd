SynthDef(\prophet, {
	|bus=0 freq=440 amp=1.0 gate=1 lforate=1 lfowidth=0.5 cutoff=6000 rq=0.4 pan=0.0, sus=0.1, fmod=0|
	var osc, lfo, pulse, filter, env;
	// Amp is way too much for foxdot
	amp = amp * 0.1;
	freq = In.kr(bus) + [0, fmod];
	lfo = LFTri.kr(lforate * [1, 1.01], Rand(0, 2.0)!2);
	pulse = Pulse.ar(freq * [1, 1.01], lfo * lfowidth + 0.5);
	osc = RLPF.ar(pulse, cutoff, rq);
	osc = BHiPass.ar(osc, 200);
	env = EnvGen.ar(Env([0,1,0.8,0.8,0], [0.01, 0, sus, sus]), doneAction:3);
	osc = Mix(osc);
	osc = osc * env * amp;
	osc =  Pan2.ar(osc, pan);
	ReplaceOut.ar(bus, osc)
},
metadata: (
	credit: "Mitchell Sigman",
	modified_by: "Bruno Ruviaro, Jens Meisner",
	description: "",
	category: \keys,
	tags: [\polyphonic, \analog, \Synthesizer]
	)
).add