finally got around to rerunning this on 0.5.0.

short version: on big flat-ish targets (flat tops, a pair of bars) the OT seed + leonardo lands at 0 vortices and ~0.97-1.00 fidelity. quadratic sits at 8-45 vortices and ~0.90-0.93. the seed costs ~0.4 s (about 14 iterations) and gets to 0.99 in a couple of iterations on the flat tops, so it pays for itself there.

on rings it doesn't help. quadratic ties or wins, and stacking remove_vortices on top of OT made things slightly worse everywhere.

fwiw remove_vortices only bites under kim (phase fixed), and kim drifts on extended targets anyway, so quadratic + removal ended up worse than plain quadratic.

agree on `method="ot"` then wgs. happy to do the cupy bit, just no gpu to test on.

script + table: [benchmark_v050.md](https://github.com/steps-re/optical-lattice-extensions/blob/main/contrib/slmsuite/benchmark_v050.md) (ai-assisted, numbers straight from the script)
