library ieee;
use ieee.std_logic_1164.all;

use work.htfft_pkg.all;
use work.htfft{{suffix}}_params.all;
use work.htfft{{suffix}}_pipeline.all;

entity htfft{{suffix}} is
 port (
   clk: in std_logic;
   reset: in std_logic;
   -- Indicates this is the first clock cycle of data for this FFT.
   i_first: in std_logic;
   i_data: in std_logic_vector(SPCC*INPUT_WIDTH-1 downto 0);
   o_first: out std_logic;
   o_data: out std_logic_vector(SPCC*OUTPUT_WIDTH-1 downto 0)
   );
end entity;

architecture arch of htfft{{suffix}} is

  constant R_WIDTH: positive := INPUT_WIDTH + 2*logceil(SPCC);

  constant UNROLLED_FFT_LATENCY: natural := BUTTERFLY_LATENCY * logceil(SPCC);

  signal p_data: std_logic_vector(INPUT_WIDTH*SPCC-1 downto 0);

  signal q_beforefirst: std_logic;
  signal q_beforefirstslv: std_logic_vector(0 downto 0);
  signal q_data: std_logic_vector(INPUT_WIDTH*SPCC-1 downto 0);

  signal r_reset: std_logic;
  signal r_beforefirstslv: std_logic_vector(0 downto 0);
  signal r_data: std_logic_vector(R_WIDTH*SPCC-1 downto 0);

  {% for index in range(n_stages+1) %}
  signal r{{loop.index0}}_reset: std_logic;
  signal r{{loop.index0}}_data_a: std_logic_vector((R_WIDTH+2*{{loop.index0}})*SPCC/2-1 downto 0);
  signal r{{loop.index0}}_data_b: std_logic_vector((R_WIDTH+2*{{loop.index0}})*SPCC/2-1 downto 0);
  {% endfor %}

  signal s_beforefirst: std_logic;
  signal s_first: std_logic;
  signal s_data: std_logic_vector(SPCC*OUTPUT_WIDTH-1 downto 0);

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
  initial_mem: entity work.initial_memory
    generic map (
      WIDTH => INPUT_WIDTH,
      SPCC => SPCC,
      N => N,
      BARREL_SHIFTER_PIPELINE => BARREL_SHIFTER_PIPELINE
      )
    port map (
      clk => clk,
      reset => reset,
      i_beforefirst => i_first,
      i_data => p_data,
      o_beforefirst => q_beforefirst,
      o_data => q_data
      );
  -- Process the data with an unrolled FFT the size of which matches
  -- the number samples arriving per clock cycle.
  unrolled: entity work.unrolled_fft_inner_{{spcc}}{{suffix}}
    port map (
      clk => clk,
      i_data => q_data,
      o_data => r_data
      );

  q_beforefirstslv(0) <= q_beforefirst;
  unrolled_sr: entity work.shift_register
    generic map (
      WIDTH => 1,
      LENGTH => UNROLLED_FFT_LATENCY
      )
    port map (
      clk => clk,
      i_data => q_beforefirstslv,
      o_data => r_beforefirstslv
      );
      
  -- Process the data with rolled FFT stages (where rolled just means storing
  -- intermediate results in memory, i.e. not unrolled).
  r0_reset <= r_beforefirstslv(0);
  r0_data_a <= r_data(R_WIDTH*SPCC/2-1 downto 0);
  r0_data_b <= r_data(R_WIDTH*SPCC-1 downto R_WIDTH*SPCC/2);
  {% for stage_n in stage_ns %}
    stage_{{stage_n}}_inst: entity work.stage_{{stage_n}}{{suffix}}
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
  final_mem: entity work.final_memory
    generic map (
      WIDTH => OUTPUT_WIDTH,
      SPCC => SPCC,
      N => N
      )
    port map (
      clk => clk,
      i_beforefirst => r{{n_stages}}_reset,
      i_data_a => r{{n_stages}}_data_a,
      i_data_b => r{{n_stages}}_data_b,
      o_beforefirst => s_beforefirst,
      o_data => s_data
      );
  process(clk)
  begin
    if rising_edge(clk) then
      s_first <= s_beforefirst;
    end if;
  end process;

  yes_reg_s_o: if REG_S_O generate
    process(clk)
    begin
      if rising_edge(clk) then
        o_first <= s_first;
        o_data <= s_data;
        if reset = '1' then
          o_first <= '0';
        end if;
      end if;
    end process;
  end generate;
  no_reg_s_o: if not REG_S_O generate
    o_first <= s_first;
    o_data <= s_data;
  end generate;
  
end architecture;
