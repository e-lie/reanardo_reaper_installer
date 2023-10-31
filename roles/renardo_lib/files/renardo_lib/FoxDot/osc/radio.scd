SynthDef.new(\radio, {
	|bus=0, freq=800, gate=1, amp=0.5, pan=0, fmod=0, rel=3, rate=1|
	var env, osc;
	freq = In.kr(bus, 1);
	freq = [freq, freq+fmod];
	env = EnvGen.ar(Env.asr(0, 1, rel), gate, doneAction: 0);
	osc = Pan2.ar(CombN.ar(Resonz.ar(Gendy5.ar(1, 40, minfreq: 0.2, maxfreq: freq, durscale: 0.1, initCPs: 10), freq * rate,0.1),0.1,0.5,0.6));
	osc = FreeVerb.ar(osc, 0.1, 0.5);
	osc = Mix(osc);
	osc = Limiter.ar(osc);
	osc = osc * env * amp * 0.5;
	osc = Splay.ar(osc, pan);
	ReplaceOut.ar(bus, osc)
},
metadata: (
	credit: "CrashServer",
	modified_by: "Jens Meisner",
	description: "",
	category: \ambient,
	tags: [\tag]
	)
).add;