library ieee;
use ieee.std_logic_1164.all;

use work.htfft{{suffix}}_pipeline.all;

-- Because VHDL recursive instantiation is not well supported by
-- tools we generate this file for different fft sizes.
entity unrolled_fft_inner_{{size}}{{suffix}} is
  port (
    clk: in std_logic;
    -- Would be nice to have array types here but
    -- we can't rely on tool support for generic packages
    -- so just use std_logic_vector.  
    i_data: in std_logic_vector({{input_width}}*{{size}}-1 downto 0);
    o_data: out std_logic_vector(({{input_width}}+2*{{logceil_size}})*{{size}}-1 downto 0)
    );
end entity;

architecture arch of unrolled_fft_inner_{{size}}{{suffix}} is
  constant INPUT_WIDTH: positive := {{input_width}};
  constant OUTPUT_WIDTH: positive := INPUT_WIDTH + 2*{{logceil_size}};
  constant INTERMED_WIDTH: positive := OUTPUT_WIDTH - 2;
  constant SIZE: positive := {{size}};
  constant TWIDDLE_WIDTH: positive := {{twiddle_width}};

  subtype t_smaller_input is std_logic_vector(INPUT_WIDTH*SIZE/2-1 downto 0);
  type array_of_smaller_input is array(natural range <>) of t_smaller_input;
  signal i_datachunked: array_of_smaller_input(1 downto 0);

  subtype t_smaller_output is std_logic_vector(INTERMED_WIDTH*SIZE/2-1 downto 0);
  type array_of_smaller_output is array(natural range <>) of t_smaller_output;
  signal a_datachunked: array_of_smaller_output(1 downto 0);

  subtype t_bfinput is std_logic_vector(INTERMED_WIDTH-1 downto 0);
  subtype t_bfoutput is std_logic_vector(OUTPUT_WIDTH-1 downto 0);
  type array_of_bfinput is array(natural range <>) of t_bfinput;
  type array_of_bfoutput is array(natural range <>) of t_bfoutput;
  signal a_dataarray: array_of_bfinput(SIZE-1 downto 0);
  signal o_dataarray: array_of_bfoutput(SIZE-1 downto 0);
  subtype t_twiddle is std_logic_vector(TWIDDLE_WIDTH-1 downto 0);
  type array_of_twiddles is array(natural range <>) of t_twiddle;

  constant LOCAL_TWIDDLES: array_of_twiddles(SIZE/2-1 downto 0) := ({% for twiddle in twiddles %}
    {{loop.index0}} => "{{twiddle}}"{% if not loop.last %},{% endif %}{% endfor %}
  );
    
begin
  {% if size > 2 %}
  loop_small_ffts: for smaller_index in 0 to 1 generate
    i_datachunked(smaller_index) <= i_data((smaller_index+1)*INPUT_WIDTH*SIZE/2-1 downto smaller_index*INPUT_WIDTH*SIZE/2);
    smaller_fft: entity work.unrolled_fft_inner_{{size//2}}{{suffix}}
      port map (
        clk => clk,
        i_data => i_datachunked(smaller_index),
        o_data => a_datachunked(smaller_index)
        );
  end generate;
  {% else %}
    i_datachunked(0) <= i_data(INPUT_WIDTH-1 downto 0);
    i_datachunked(1) <= i_data(2*INPUT_WIDTH-1 downto INPUT_WIDTH);
    a_datachunked(0) <= i_datachunked(0);
    a_datachunked(1) <= i_datachunked(1);
  {% endif %}

  loop_butterflys: for bf_index in 0 to SIZE/2-1 generate
    a_dataarray(bf_index) <= a_datachunked(0)((bf_index+1)*INTERMED_WIDTH-1 downto bf_index*INTERMED_WIDTH);
    a_dataarray(bf_index+SIZE/2) <= a_datachunked(1)((bf_index+1)*INTERMED_WIDTH-1 downto bf_index*INTERMED_WIDTH);
    bf: entity work.butterfly
      generic map (
        WIDTH => INTERMED_WIDTH,
        TWIDDLE_WIDTH => TWIDDLE_WIDTH,
        MULT_LATENCY => MULT_LATENCY,
        REG_I_P => BUTTERFLY_I_P,
        REG_Q_R => BUTTERFLY_Q_R,
        REG_R_S => BUTTERFLY_R_S,
        REG_S_O => BUTTERFLY_S_O
      )
      port map (
        clk => clk,
        i_a => a_dataarray(bf_index),
        i_b => a_dataarray(bf_index+SIZE/2),
        i_t => LOCAL_TWIDDLES(bf_index),
        o_c => o_dataarray(bf_index),
        o_d => o_dataarray(bf_index+SIZE/2)
        );
    o_data((bf_index+1)*OUTPUT_WIDTH-1 downto bf_index*OUTPUT_WIDTH) <=
      std_logic_vector(o_dataarray(bf_index));
    o_data((bf_index+SIZE/2+1)*OUTPUT_WIDTH-1 downto (bf_index+SIZE/2)*OUTPUT_WIDTH) <=
      std_logic_vector(o_dataarray(bf_index+SIZE/2));
  end generate;

end architecture;

