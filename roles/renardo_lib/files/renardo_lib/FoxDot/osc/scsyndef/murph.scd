

// We generate 4 consecutive random wavetables using an env
// consecutive buffers are necessary for VOsc to work;
(

~wavetables = Array.fill(4, {
	var numSegs = rrand(4,20);
	Env(
		[0]++({rrand(0.0,1.0)}!numSegs-1)++[0],
		{exprand(1,20)}!numSegs,
		{rrand(-20,20)}!numSegs,
	).asSignal(1024).asWavetable;
});

~buffers = Buffer.allocConsecutive(4, s, 2048);

~buffers.do({
	arg buf, i;
	buf.loadCollection(~wavetables[i]);
}
);

SynthDef.new(\murph, {
	// arg out=0, buf=0, numBufs=2, freq=300, amp=0.2;
	arg amp=1, sus=1, pan=0, buf=0, numBufs=2, freq=300, vib=0, fmod=0, rate=0, bus=0, blur=1, beat_dur=1, atk=0.01, decay=0.01, rel=0.01, peak=1, level=0.8;
	var sig, bufpos, detuneSig;
	detuneSig = LFNoise1.kr(0.2!8).bipolar(0.2).midiratio;
	bufpos = buf + LFNoise1.kr(0.5).range(0, numBufs-1);
	sig = VOsc.ar(bufpos, freq*detuneSig);
	sig = Splay.ar(sig);
	sig = LeakDC.ar(sig) * amp * 0.2;
	env=EnvGen.ar(Env.perc(attackTime: atk,releaseTime: sus,level: amp,curve: 'lin'), doneAction: 2);
	sig = sig * env;
	// Out.ar(out, sig);
	ReplaceOut.ar(bus, sig);
}).add;

)
