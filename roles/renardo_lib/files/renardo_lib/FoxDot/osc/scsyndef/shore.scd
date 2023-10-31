SynthDef.new(\shore, {
	|bus=0, dur=1, amp=1, atk=1, sus=1, rel=0.7, fmod=0, freq=0, pan=0, coef=0.6, noiselevel=0.1, density=100, mdust=0.5|
	var osc, env, atk_fil;
	freq = In.kr(bus, 1);
	freq = [freq, freq+fmod];
	env = EnvGen.kr(Env.asr(atk, sus, rel, curve: \sqr), doneAction: 0);
	osc = OnePole.ar(WhiteNoise.ar(noiselevel) + Dust.ar(density, mul: mdust), coef: coef, mul:1);
	osc = osc + Splay.ar(FreqShift.ar(osc, 1/(4..9))) * env;
	osc = Mix(osc);
	osc = osc * amp * 1;
	osc = Pan2.ar(osc,pan);
	ReplaceOut.ar(bus,osc)
},
metadata: (
	credit: "Credit",
	modified_by: "Modifier",
	decription: "Description",
	category: \category,
	tags: [\tag, \tag]
)).add;