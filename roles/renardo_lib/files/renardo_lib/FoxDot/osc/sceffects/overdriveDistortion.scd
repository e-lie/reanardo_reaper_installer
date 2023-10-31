SynthDef.new(\overdriveDistortion,
{|bus, drive|
var osc;
osc = In.ar(bus, 2);
osc = (osc * (drive * 50)).clip(0,0.2).fold2(2);
osc = Compander.ar(osc, osc, thresh: comp, slopeAbove: comp_down, slopeBelow: comp_up, clampTime: 0.01, relaxTime: 0.01, mul: 1);
ReplaceOut.ar(bus, osc)}).add;