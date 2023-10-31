SynthDef.new(\scrap, {
	|vib=0, bus=0, slide=0, rate=1, atk=0.01, sus=1, rel=0.6, slidefrom=1, fmod=0, amp=1, freq=0, bits=0, pan=0|
	var osc, env, vibr;
	freq = In.kr(bus, 1);
	freq = [freq, freq+fmod];
	osc = SinOsc.ar(Line.ar(freq * slidefrom,freq * (1 + slide) ), mul: 1);
	vibr = Vibrato.kr(osc, rate: vib);
	env = EnvGen.kr(Env.linen(atk, sus, rel, curve: -4), doneAction: 0);
	osc = Mix(osc);
	osc = osc * env * amp * 0.15;
	osc = Pan2.ar(osc, pan);
	ReplaceOut.ar(bus, osc)
},
metadata: (
	credit: "Credit",
	modified_by: "Modifier",
	decription: "Description",
	category: \category,
	tags: [\tag, \tag]
)).add;
