HDL Thoughts
============

One of the purposes of creating this open-source core was to have a concrete
public example to use as a reference when expressing frustrations with
gateware design processes.

Some of the things that annoy me about the way I went about implementing this
design are:


Problem 1):
   The generation is messy.  Using a templating language like Jinja2 is an ugly
   way to make code generic.
Solution:
   Maybe it would be better to use a language like migen or chisel.  If we're
   going to be generating the vhdl anyway, it might be simpler to use a
   language that is designed with that in mind.
   
Problem 2):
   Proving the equivalence of the hardware with a mathmatical description of
   the algorithm, or a software implementation is very difficult.
Solution:
   Don't know of any good solutions. It feels like it would be nice to
   be able to write a proof that gradually transforms the math into the
   hardware.  Doesn't need to be automatically generated, but does need to
   be automatically checked.
   
Problem 3):
   The produced code is only VHDL, but some projects might need verilog.
Solution:
   One possible solution is the same as (1), use migen or chisel and then
   generate verilog or VHDL depending on what is required.  Another possible
   solution is to generate verilog from the VHDL using ghdl synth.
   
Problem 4):
   When thinking about the algorithm we're thinking about vectors, but this
   abstraction level is only present in the VHDL in the 'first' signals
   that indicating this is the first piece of a vector.  It would be
   nice to have a language where I can reason about the vectors at a high
   level, but still get the low level control over the pipelining and
   implementation details.
Solution:
   ?????
   


   
