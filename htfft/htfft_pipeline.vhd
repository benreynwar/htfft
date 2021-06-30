use work.htfft_pkg.all;

package htfft{{suffix}}_pipeline is

  constant BARREL_SHIFTER_PIPELINE: string := "{{pipelines.barrel_shifter}}";
  constant MULT_LATENCY: positive := {{pipelines.butterfly.mult_latency}};
  constant BUTTERFLY_I_P: boolean := {{ 'true' if pipelines.butterfly.reg_i_p else 'false' }};
  constant BUTTERFLY_Q_R: boolean := {{ 'true' if pipelines.butterfly.reg_q_r else 'false' }};
  constant BUTTERFLY_R_S: boolean := {{ 'true' if pipelines.butterfly.reg_r_s else 'false' }};
  constant BUTTERFLY_S_O: boolean := {{ 'true' if pipelines.butterfly.reg_s_o else 'false' }};
  constant BUTTERFLY_LATENCY: positive :=
      MULT_LATENCY +
      boolean_to_int(BUTTERFLY_I_P) + 
      boolean_to_int(BUTTERFLY_Q_R) + 
      boolean_to_int(BUTTERFLY_R_S) + 
      boolean_to_int(BUTTERFLY_S_O);

end package;
