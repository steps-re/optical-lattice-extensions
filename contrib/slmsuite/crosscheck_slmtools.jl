# Cross-check harness: run SLMTools' own otPhase + gs on inputs replicated
# exactly in Python, and dump everything for comparison.
using SLMTools, DelimitedFiles

n = 64
L  = natlat((n, n))                 # self-dual natural lattice, flambda = 1
dL = dualShiftLattice(L, 1.0)
s  = sqrt(n)                        # px -> natural units

# Input: Gaussian amplitude waist 15 px (intensity = amp^2).
wnat = 15 / s
Uarr = [exp(-2 * (x^2 + y^2) / wnat^2) for x in L[1], y in L[2]]
U = LF{Intensity}(Uarr, L, 1.0)

# Target: smoothed square flat-top, half-width 20 px, edge 2 px, tail clamped.
hw, ed = 20 / s, 2 / s
Varr = [0.5 * (1 - tanh((max(abs(x), abs(y)) - hw) / ed)) for x in dL[1], y in dL[2]]
Varr[Varr .< maximum(Varr) * 0.01] .= 0
V = LF{Intensity}(Varr, dL, 1.0)

t0 = time()
Phi = otPhase(U, V, 0.001)          # RealPhase, units of cycles
println("otPhase: $(round(time()-t0, digits=1)) s")

t0 = time()
Pgs = gs(sqrt(U), sqrt(V), 100, Phi)
println("gs(100): $(round(time()-t0, digits=1)) s")

# Translation control: same Gaussian shifted by 8 px.
sh = 8 / s
V2 = LF{Intensity}([exp(-2 * ((x - sh)^2 + y^2) / wnat^2) for x in dL[1], y in dL[2]], dL, 1.0)
Phi2 = otPhase(U, V2, 0.001)

writedlm("cc_U.csv", Uarr, ',')
writedlm("cc_V.csv", Varr, ',')
writedlm("cc_phi.csv", Phi.data, ',')
writedlm("cc_phigs.csv", angle.(Pgs.data), ',')
writedlm("cc_phi_shift.csv", Phi2.data, ',')
println("wrote cc_*.csv")
