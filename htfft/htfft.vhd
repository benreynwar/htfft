library ieee;
use ieee.std_logic_1164.all;

entity htfft{{suffix}} is
 port (
   clk: in std_logic;
   -- Indicates this is the first clock cycle of data for this FFT.
   i_first: in std_logic;
   i_data: in std_logic_vector({{size}}*{{input_width}}-1 downto 0);
   o_data: out std_logic_vector({{size}}*{{output_width}}-1 downto 0)
   );
end entity;

architecture arch of htfft is
  constant INPUT_WIDTH: positive := {{input_width}};
  constant N: positive := {{n}};
  constant SIZE: positive := {{size}};
begin

  process(clk)
  begin
    if rising_edge(clk) then
      -- We're mostly have this delay in so that i_first can arrive
      -- one clock cycle ahead so it can act like a reset to prepare
      -- for the new vector.
      p_data <= i_data;
    end if;
  end process;

  -- Do the initial reordering of the input data.
  initial: entity work.initial_memory
    port map (
      clk => clk,
      i_reset => i_first,
      i_data => p_data,
      o_data => q_data
      );
  -- Process the data with an unrolled FFT the size of which matches
  -- the number samples arriving per clock cycle.
  unrolled: entity work.unrolled_fft_inner_{{size}}{{suffix}}
    port map (
      clk => clk,
      i_data => q_data,
      o_data => r_data
      );
  -- Process the data with rolled FFT stages (where rolled just means storing
  -- intermediate results in memory, i.e. not unrolled).
  {% for stage_n in stage_ns %}
    stage_{{stage_n}}_inst: stage_{{stage_n}}{{suffix}}
    port map (
      clk => clk,
      i_reset => r{{loop.index0}}_reset,
      i_data_a => r{{loop.index0}}_data_a,
      i_data_b => r{{loop.index0}}_data_b,
      o_reset => r{{loop.index0+1}}_reset, 
      o_data_a => r{{loop.index0+1}}_data_a,
      o_data_b => r{{loop.index0+1}}_data_b
   );
  {% endfor %}
  -- Do the final reordering of the output data.
  s_reset <= r{{n_stages}}_reset;
  s_data(SIZE/2*OUTPUT_WIDTH-1 downto 0) <= r{{n_stages}}_data_a;
  s_data(SIZE*OUTPUT_WIDTH-1 downto SIZE/2*OUTPUT_WIDTH) <= r{{n_stages}}_data_b;
  initial: entity work.final_memory
    port map (
      clk => clk,
      i_reset => s_reset,
      i_data => s_data,
      o_data => o_data
      );
  
end architecture;
