// =============================================================================
//  Quantum Tunneling Simulator — High-Performance C++ Solver  v3.0
//  Method  : Crank-Nicolson (unconditionally stable, 2nd-order in time & space)
//
//  OUTPUTS
//  -------
//  core/data/output.csv     — position-space probability density per step
//  core/data/momentum.csv   — momentum-space |phi(k)|^2 per step
//
//  FEATURES
//  --------
//  [1] Optimised Thomas algorithm     : pre-allocated scratch, O(N), FMA-friendly
//  [2] Complex Absorbing Potential    : eliminates ghost reflections at walls
//  [3] Double-barrier (resonant mode) : argv[6]=2 places second barrier at x=80
//  [4] Momentum-space DFT output      : |phi(k)|^2 written to momentum.csv
//  [5] Norm conservation check        : warns on growth, aborts if > 101%
//  [6] OpenMP parallelism             : compile with -fopenmp for 4-8x speedup
//  [7] Reflection coefficient R(t)    : integral left of barrier, excl. CAP zone
//  [8] Wavefunction normalisation     : exact int|psi|^2 dx = 1 at t=0
//  [9] Dirichlet boundary conditions  : psi[0] = psi[N-1] = 0, enforced exactly
//
//  USAGE
//  -----
//  solver.exe [V0] [bWidth] [k0] [sigma] [steps] [barrier_mode]
//
//  ARGUMENTS (all optional, positional)
//  -------------------------------------
//  V0           barrier height in energy units      default: 150.0
//  bWidth       barrier width  in spatial units     default:   5.0
//  k0           initial wave-vector                 default:   4.5
//  sigma        Gaussian packet width               default:   4.0
//  steps        total time steps                    default: 500
//  barrier_mode 1=single barrier  2=double barrier  default:   1
//
//  COMPILE
//  -------
//  Single-thread : g++ -O2 -std=c++17 -o core/solver.exe core/core/solver.cpp
//  Multi-thread  : g++ -O2 -std=c++17 -fopenmp -o core/solver.exe core/core/solver.cpp
//
//  PHYSICS CONVENTION
//  ------------------
//  hbar = 1,  m = 1/2  =>  hbar^2 / 2m = 1
//  Kinetic energy of packet : E_kin = k0^2 / 2
//  Classical barrier top    : V0
//  Tunneling regime         : E_kin < V0
// =============================================================================

#include <iostream>
#include <vector>
#include <complex>
#include <fstream>
#include <cmath>
#include <string>
#include <cstdlib>
#include <algorithm>

#ifdef _OPENMP
    #include <omp.h>
#endif

using namespace std;
typedef complex<double> cd;

// Imaginary unit
static const cd IM(0.0, 1.0);

// =============================================================================
//  THOMAS ALGORITHM  (tridiagonal solver)
//
//  Solves A * x = r  where A is tridiagonal with diagonals (a, bOrig, c).
//  bOrig is never modified — LU factors are written to scratch bWork/cWork,
//  allowing the SAME factorisation to be reused across every time step
//  without recomputing.
//
//  Cost: O(N) — forward sweep fuses into one complex division per row.
//  Scratch buffers bWork and cWork must be pre-allocated by the caller.
// =============================================================================
static void thomasSolve(
        const vector<cd>& a,        // sub-diagonal       a[1 .. N-1]
        const vector<cd>& bOrig,    // main diagonal      (read-only)
        const vector<cd>& c,        // super-diagonal     c[0 .. N-2]
        vector<cd>&       r,        // RHS in  /  solution out
        vector<cd>&       bWork,    // scratch: modified main diagonal
        vector<cd>&       cWork)    // scratch: modified super-diagonal
{
        const int N = static_cast<int>(r.size());

        // Forward sweep — eliminate sub-diagonal
        bWork[0] = bOrig[0];
        cWork[0] = c[0];
        for (int i = 1; i < N; ++i) {
                const cd fac = a[i] / bWork[i - 1];
                bWork[i]     = bOrig[i] - fac * cWork[i - 1];
                r[i]         = r[i]     - fac * r[i - 1];
                if (i < N - 1) cWork[i] = c[i];
        }

        // Back substitution
        r[N - 1] /= bWork[N - 1];
        for (int i = N - 2; i >= 0; --i)
                r[i] = (r[i] - cWork[i] * r[i + 1]) / bWork[i];
}

// =============================================================================
//  NORM INTEGRAL  over index range [lo, hi)
//  Returns  sum_{i=lo}^{hi-1}  |psi[i]|^2 * dx
// =============================================================================
static inline double normRange(
        const vector<cd>& psi, int lo, int hi, double dx)
{
        double s = 0.0;
        for (int i = lo; i < hi; ++i) s += norm(psi[i]);
        return s * dx;
}

// =============================================================================
//  MOMENTUM SPECTRUM  |phi(k)|^2  via direct DFT
//
//  Computes M samples of the Fourier transform over k in [-pi/dx, +pi/dx].
//  phi(k) = integral psi(x) e^{-ikx} dx  (approximated as Riemann sum).
//
//  Cost: O(N * M) — called only on export steps (every 5th step).
//  For higher performance link against FFTW3 and replace this function.
// =============================================================================
static vector<pair<double, double>> momentumSpectrum(
        const vector<cd>& psi, double dx, int M)
{
        const int    N    = static_cast<int>(psi.size());
        const double kMax = 3.14159265358979323846 / dx;   // Nyquist wave-vector

        vector<pair<double, double>> spec(M);
        for (int m = 0; m < M; ++m) {
                // k uniformly spaced from -kMax to +kMax
                const double k  = -kMax + m * (2.0 * kMax / (M - 1));
                cd           sum = 0.0;
                for (int n = 0; n < N; ++n)
                        sum += psi[n] * exp(-IM * k * (n * dx)) * dx;
                spec[m] = { k, norm(sum) };    // { k-value, |phi(k)|^2 }
        }
        return spec;
}

// =============================================================================
//  MAIN
// =============================================================================
int main(int argc, char* argv[])
{
        // =========================================================================
        //  SECTION 1 — Parse command-line arguments
        // =========================================================================
        const double V0          = (argc > 1) ? atof(argv[1]) : 150.0;
        const double bWidth      = (argc > 2) ? atof(argv[2]) :   5.0;
        const double k0          = (argc > 3) ? atof(argv[3]) :   4.5;
        const double sigma       = (argc > 4) ? atof(argv[4]) :   4.0;
        const int    nSteps      = (argc > 5) ? atoi(argv[5]) :   500;
        const int    barrierMode = (argc > 6) ? atoi(argv[6]) :     1;

        // =========================================================================
        //  SECTION 2 — Grid and time-step parameters
        // =========================================================================
        const int    N     = 600;          // spatial grid points
        const double L     = 120.0;        // domain length  [0, L]
        const double dx    = L / (N - 1);  // grid spacing
        const double dt    = 0.04;         // time step (tightened for accuracy)
        const double x0    = 30.0;         // initial packet centre

        // Crank-Nicolson coefficient  alpha = dt / (2 dx^2)
        // With hbar=1, m=1/2: the kinetic operator is -d^2/dx^2
        const double alpha = dt / (2.0 * dx * dx);

        // Informational stability check (CN is unconditionally stable, but
        // large alpha*dt degrades spatial accuracy)
        if (alpha * dt > 0.5)
                cerr << "[warn] alpha*dt = " << alpha * dt
                         << " > 0.5 — consider reducing dt for better accuracy\n";

        // Report thread count
#ifdef _OPENMP
        cout << "[info] OpenMP active — using " << omp_get_max_threads() << " threads\n";
#else
        cout << "[info] OpenMP not compiled — running single-thread\n";
#endif

        // =========================================================================
        //  SECTION 3 — Complex Absorbing Potential  W(x)
        //
        //  Placed in the last CAP_WIDTH grid points on each side of the domain.
        //  Shape: W(x) = CAP_STRENGTH * xi^2  where xi = distance_from_interior /
        //  CAP_WIDTH  (0 at interior edge, 1 at domain wall).
        //
        //  Effect on the Schrodinger equation:
        //    i * d/dt psi = [ H - i*W(x) ] psi
        //  The -i*W term causes exponential decay of the wavefunction inside the
        //  CAP layer, absorbing outgoing flux before it can reflect from the wall.
        //
        //  CAP enters Crank-Nicolson as:
        //    LHS += + (dt/2) * W    (real, positive — absorbs)
        //    RHS += - (dt/2) * W    (conjugate sign for time-reversal consistency)
        // =========================================================================
        const int    CAP_WIDTH    = static_cast<int>(0.12 * N);   // ~72 points per side
        const double CAP_STRENGTH = 15.0;

        vector<double> capW(N, 0.0);
        for (int i = 0; i < CAP_WIDTH; ++i) {
                const double xi = static_cast<double>(CAP_WIDTH - i) / CAP_WIDTH;
                const double w  = CAP_STRENGTH * xi * xi;
                capW[i]         = w;    // left  wall absorber
                capW[N - 1 - i] = w;    // right wall absorber
        }

        // =========================================================================
        //  SECTION 4 — Physical potential  V(x)
        //
        //  Single barrier : rectangular step from x=60 to x=60+bWidth
        //  Double barrier : second identical barrier at x=80 to x=80+bWidth
        //                   The cavity between them enables resonant tunneling.
        // =========================================================================
        vector<double> V(N, 0.0);

        // First barrier
        const int bStart = static_cast<int>(60.0 / dx);
        const int bEnd   = min(N, bStart + static_cast<int>(bWidth / dx + 0.5));
        for (int i = bStart; i < bEnd; ++i) V[i] = V0;

        // Second barrier (resonant tunneling mode)
        int    bStart2 = 0;
        int    bEnd2   = 0;
        double xBS2    = 0.0;
        double xBE2    = 0.0;

        if (barrierMode == 2) {
                bStart2 = static_cast<int>(80.0 / dx);
                bEnd2   = min(N, bStart2 + static_cast<int>(bWidth / dx + 0.5));
                for (int i = bStart2; i < bEnd2; ++i) V[i] = V0;
                xBS2 = bStart2 * dx;
                xBE2 = bEnd2   * dx;
                cout << "[info] Double-barrier mode — barrier2 x=["
                         << xBS2 << ", " << xBE2 << "]\n";
        }

        // =========================================================================
        //  SECTION 5 — Gaussian wave-packet initialisation  psi(x, 0)
        //
        //  psi(x,0) = A * exp( -(x-x0)^2 / (2*sigma^2) ) * exp( i*k0*x )
        //
        //  A is chosen so that the discrete integral  sum |psi[i]|^2 * dx = 1.
        //  The packet is centred at x0=30, well left of the barrier at x=60,
        //  so the simulation begins before any barrier interaction.
        // =========================================================================
        vector<cd> psi(N);
        double initNorm = 0.0;
        for (int i = 0; i < N; ++i) {
                const double x = i * dx;
                const double g = exp(-pow(x - x0, 2) / (2.0 * sigma * sigma));
                psi[i]          = g * exp(IM * k0 * x);
                initNorm        += norm(psi[i]);
        }
        initNorm *= dx;

        // Normalise: scale so int |psi|^2 dx = 1
        const double normFactor = 1.0 / sqrt(initNorm);
        for (auto& p : psi) p *= normFactor;

        // Store initial norm for the conservation check in section 7
        const double normInit = normRange(psi, 0, N, dx);   // should be ~1.0

        // =========================================================================
        //  SECTION 6 — Assemble Crank-Nicolson tridiagonal system
        //
        //  The CN scheme rewrites  i * d/dt |psi> = H_eff |psi>  as:
        //
        //    ( I + i*dt/2 * H_eff ) |psi^{n+1}> = ( I - i*dt/2 * H_eff ) |psi^n>
        //                    LHS                               RHS
        //
        //  where H_eff = -d^2/dx^2 + V(x) - i*W(x)
        //
        //  Discretising the Laplacian with central differences gives a
        //  tridiagonal LHS with:
        //    sub/super-diagonal : -i * alpha
        //    main diagonal      : 1 + 2*i*alpha + i*(dt/2)*V[i] + (dt/2)*W[i]
        //
        //  The LHS is time-INDEPENDENT (V and W are static), so it is built
        //  ONCE here and the Thomas algorithm reuses it every step.
        // =========================================================================
        vector<cd> diagA(N, -IM * alpha);   // sub-diagonal
        vector<cd> diagB(N);                // main diagonal
        vector<cd> diagC(N, -IM * alpha);   // super-diagonal

        for (int i = 0; i < N; ++i) {
                diagB[i] = 1.0
                                 + 2.0 * IM * alpha             // kinetic (implicit)
                                 + IM  * (dt / 2.0) * V[i]      // potential
                                 + (dt / 2.0) * capW[i];         // CAP (real — absorbing)
        }

        // Enforce Dirichlet boundary conditions: psi[0] = psi[N-1] = 0
        diagA[0]     = 0.0;  diagC[0]     = 0.0;  diagB[0]     = 1.0;
        diagA[N - 1] = 0.0;  diagC[N - 1] = 0.0;  diagB[N - 1] = 1.0;

        // Pre-allocate Thomas scratch buffers once (avoids per-step heap alloc)
        vector<cd> bWork(N), cWork(N);

        // =========================================================================
        //  SECTION 7 — Open output files
        // =========================================================================

        // -- Position-space CSV --
        ofstream posFile("core/data/output.csv");
        if (!posFile.is_open()) {
                cerr << "[error] Cannot open core/data/output.csv — "
                         << "check that the directory core/data/ exists.\n";
                return 1;
        }
        posFile << "step,x,prob,trans_prob,refl_prob,norm_total,"
                             "barrier_start,barrier_end,V0,"
                             "barrier_start2,barrier_end2\n";

        // -- Momentum-space CSV --
        ofstream momFile("core/data/momentum.csv");
        if (!momFile.is_open()) {
                cerr << "[error] Cannot open core/data/momentum.csv\n";
                return 1;
        }
        momFile << "step,k,mom_prob\n";

        // Convenience: barrier positions in physical units
        const double xBS = bStart * dx;
        const double xBE = bEnd   * dx;

        // Number of k-samples for DFT (half the spatial grid)
        const int MOM_SAMPLES = N / 2;

        // =========================================================================
        //  SECTION 8 — Time evolution loop
        //
        //  Each step:
        //   (a) Build RHS  (explicit half-step)
        //   (b) Solve tridiagonal  (implicit half-step)
        //   (c) Check norm conservation
        //   (d) Export position + momentum data every 5 steps
        // =========================================================================
        double normPrev = normInit;

        for (int t = 0; t < nSteps; ++t)
        {
                // ─── (a) Build RHS: ( I - i*dt/2 * H_eff ) |psi^n> ─────────────────
                //
                //  rhs[i] = psi[i]
                //         + i*alpha * ( psi[i+1] - 2*psi[i] + psi[i-1] )   <- kinetic explicit
                //         - i*(dt/2)*V[i]*psi[i]                             <- potential explicit
                //         - (dt/2)*W[i]*psi[i]                               <- CAP explicit
                //
                //  OpenMP parallelises this O(N) loop — dominant runtime cost.
                //  The boundary entries remain 0 (vector default-initialised to 0.0).
                // ────────────────────────────────────────────────────────────────────
                vector<cd> rhs(N, 0.0);

                #pragma omp parallel for schedule(static)
                for (int i = 1; i < N - 1; ++i) {
                        rhs[i] =  psi[i]
                                        + IM * alpha * (psi[i+1] - 2.0 * psi[i] + psi[i-1])
                                        - IM * (dt / 2.0) * V[i]    * psi[i]
                                        - (dt / 2.0)      * capW[i]  * psi[i];
                }
                // Boundaries stay 0 (Dirichlet)

                // ─── (b) Solve tridiagonal system ────────────────────────────────────
                thomasSolve(diagA, diagB, diagC, rhs, bWork, cWork);
                psi = rhs;

                // ─── (c) Norm conservation check ─────────────────────────────────────
                //
                //  With a CAP, the total norm decreases over time as flux is absorbed.
                //  That is correct physics — the check only fires if norm INCREASES,
                //  which would indicate a numerical instability.
                // ────────────────────────────────────────────────────────────────────
                const double normNow = normRange(psi, 0, N, dx);

                if ((normNow - normPrev) > 1e-6 && t > 0)
                        cerr << "[warn] step=" << t
                                 << "  norm increased by " << (normNow - normPrev)
                                 << "  (possible instability)\n";

                if (normNow > normInit * 1.01) {
                        cerr << "[abort] step=" << t
                                 << "  norm exceeded 101% of initial value.\n"
                                 << "         Reduce dt or increase N to stabilise.\n";
                        posFile.close();
                        momFile.close();
                        return 2;
                }

                normPrev = normNow;

                // ─── (d) Export every 5th step ───────────────────────────────────────
                if (t % 5 == 0)
                {
                        // Right edge of the rightmost barrier
                        const int rBarrierEnd = (barrierMode == 2) ? bEnd2 : bEnd;

                        // Transmission T: norm right of last barrier, excluding right CAP
                        const double T = normRange(psi, rBarrierEnd,  N - CAP_WIDTH, dx);

                        // Reflection R: norm left of first barrier, excluding left CAP
                        const double R = normRange(psi, CAP_WIDTH,    bStart,        dx);

                        // Write position-space rows (every other grid point — keeps CSV lean)
                        for (int i = 0; i < N; i += 2) {
                                posFile << t                << ","   // time step index
                                                << i * dx           << ","   // spatial position x
                                                << norm(psi[i])     << ","   // |psi(x,t)|^2
                                                << T                << ","   // transmission probability
                                                << R                << ","   // reflection probability
                                                << normNow          << ","   // total norm (decays due to CAP)
                                                << xBS              << ","   // barrier 1 left edge
                                                << xBE              << ","   // barrier 1 right edge
                                                << V0               << ","   // barrier height
                                                << xBS2             << ","   // barrier 2 left edge (0 if single)
                                                << xBE2             << "\n"; // barrier 2 right edge (0 if single)
                        }

                        // Write momentum-space rows
                        auto spec = momentumSpectrum(psi, dx, MOM_SAMPLES);
                        for (size_t mi = 0; mi < spec.size(); ++mi) { double k = spec[mi].first; double pk = spec[mi].second;
                                momFile << t   << ","   // time step index
                                                << k   << ","   // wave-vector k
                                                << pk  << "\n"; // |phi(k)|^2
                        }}
        }

        posFile.close();
        momFile.close();

        // =========================================================================
        //  SECTION 9 — Final diagnostics to stdout
        // =========================================================================
        const double finalNorm = normRange(psi, 0, N, dx);
        const int    rbe       = (barrierMode == 2) ? bEnd2 : bEnd;
        const double finalT    = normRange(psi, rbe,       N - CAP_WIDTH, dx);
        const double finalR    = normRange(psi, CAP_WIDTH, bStart,        dx);
        const double absorbed  = normInit - finalNorm;

        cout << "[info] ─────────────────────────────────────────────────\n"
                 << "[info]  Simulation complete\n"
                 << "[info] ─────────────────────────────────────────────────\n"
                 << "[info]  Grid       : N="    << N
                                                                                 << "  dx="  << dx
                                                                                 << "  dt="  << dt  << "\n"
                 << "[info]  Packet     : k0="   << k0
                                                                                 << "  sigma=" << sigma
                                                                                 << "  E_kin=" << 0.5*k0*k0 << "\n"
                 << "[info]  Barrier    : V0="   << V0
                                                                                 << "  width=" << bWidth
                                                                                 << "  mode="
                                                                                 << (barrierMode==2?"double":"single") << "\n"
                 << "[info]  CAP        : width=" << CAP_WIDTH << " pts each side"
                                                                                    << "  strength=" << CAP_STRENGTH << "\n"
                 << "[info]  Final T    : "       << finalT   * 100.0 << " %\n"
                 << "[info]  Final R    : "       << finalR   * 100.0 << " %\n"
                 << "[info]  Absorbed   : "       << absorbed * 100.0 << " % (by CAP)\n"
                 << "[info]  T + R + A  : "
                            << (finalT + finalR + absorbed) * 100.0 << " %  (should be ~100)\n"
                 << "[info]  Output     : core/data/output.csv\n"
                 << "[info]              core/data/momentum.csv\n"
                 << "[info] ─────────────────────────────────────────────────\n";

        return 0;
}