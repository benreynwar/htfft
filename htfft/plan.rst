FFT Regimes
-----------

Very low throughput: less than 1 sample per clock cycle.  Not going to look at.

Low throughput: 1 sample per clock cycle (SPCC).  Would like my solution to work for this.

Medium throughput: 1 < SPCC < N (where N is FFT size).  Would like my solution to work for this.

High thorughput: SPCC == N. Would like my solution to work for this.

Plan
----

To keep things simple keep N as a power of 2.  Keep SPCC as a power of 2.

Go with a simple radix-2 decimation-in-time FFT Cooley-Turkey so I can focus on the hardware not
the math.

Implement a medium throughput solution that since this is really a mix of the low throughput and
high throughput solutions and should generalize to both.

There will be three regimes within the FFT hardware.

There will be a fully unrolled FFT (high throughput) solution corresponding to a SPCC size FFT.

There will be a region where we're storing intermediate results in a deep memory and accessing them
like we would in a low throughput solution.

There will a a region between these two, where our memory access doesn't justify a deep memory and
we'll want to use flipflops.
Potentially on an FPGA they will be a LUTRAM-using regime between the flipflop and BRAM regimes as well.

Initially don't customize the multiplication for the target.  Just assume that the multiplication will
fit, and add some pipeline stages afterwards that retiming can use.

Break up
--------

Implement fully-unrolled FFT solution.
Implement BRAM using FFT solution.
Tie them together into a medium throughput solution.
Add intermediate regimes as time allows.

