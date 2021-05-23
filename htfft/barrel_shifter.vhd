library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.htfft_pkg.all;

entity barrel_shifter is
  -- Takes a `i_data` input and barrel shifts it by
  -- SHIFT_INCREMENT*`i_shift` bits.
  -- Implements using logceil(SIZE) stages of SIZE*2-muxes.
  -- PIPELINE specifies where to put the registers.
  -- If you're implementing on a FPGA with 6-LUTs then it can
  -- support a 4-mux in a single LUT, so make sure that you have
  -- two stages between each register.

  -- e.g. For SIZE = 64 the PIPELINE has length 7 (input, output,
  -- and registers between the 6 stages).
  -- A sensible choice for maximum frequency would be "1010101".
  -- This would be flipflop/LUT/flipflop/LUT/fliplop/LUT/flipflop.

  generic (
    -- The minimum number of bits to shift.
    SHIFT_INCREMENT: positive;
    -- The total width/shift_increment
    SIZE: positive;
    -- A string representing where the pipeline stages are.
    -- A '1' represents a pipeline stage at this location.
    -- A '0' represents no pipeline stages.
    -- Really this should be an array of boolean but many tools
    -- would have issues with that as a generic parameter.
    -- Possibility for a pipeline stage before first stage, after
    -- last stage and between any two stages.
    PIPELINE: string
    );
  port (
    clk: in std_logic;
    i_data: in std_logic_vector(SHIFT_INCREMENT*SIZE-1 downto 0);
    i_shift: in unsigned(logceil(SIZE)-1 downto 0);
    o_data: out std_logic_vector(SHIFT_INCREMENT*SIZE-1 downto 0)
    );
end entity;

architecture arch of barrel_shifter is
  constant N_STAGES: positive := logceil(SIZE);
  subtype t_chunk is std_logic_vector(SHIFT_INCREMENT-1 downto 0);
  type array_of_chunks is array(natural range <>) of t_chunk;
  subtype t_data is array_of_chunks(SIZE-1 downto 0);
  type array_of_data is array(natural range <>) of t_data;
  signal stage_indata: array_of_data(N_STAGES-1 downto 0);
  subtype t_widedata is array_of_chunks(2*SIZE-1 downto 0);
  type array_of_widedata is array(natural range <>) of t_widedata;
  signal stage_inwidedata: array_of_widedata(N_STAGES-1 downto 0);
  signal stage_outdata: array_of_data(N_STAGES-1 downto 0);
  subtype t_shift is unsigned(logceil(SIZE)-1 downto 0);
  type array_of_shift is array(natural range <>) of t_shift;
  signal stage_shift: array_of_shift(N_STAGES-1 downto 0);
  signal a_data: std_logic_vector(SIZE*SHIFT_INCREMENT-1 downto 0);
  signal a_shift: t_shift;
  signal b_data: std_logic_vector(SIZE*SHIFT_INCREMENT-1 downto 0);

  -- Shifting the string into a zero-indexed string so I don't get confused by
  -- a mixture of 1-indexing and 0-indexing.
  constant PIPELINE_ZEROINDEX: string(0 to logceil(SIZE)) := PIPELINE;
begin

  assert SIZE >= 2 severity failure;
  -- SIZE must be a power of two.
  assert 2**logceil(SIZE) = SIZE severity failure;
  -- PIPELINE generic must contain only "1" or "0" and have the correct length.
  assert PIPELINE'length = logceil(SIZE)+1 severity failure;
  check_pipeline: for pipeline_index in 0 to N_STAGES generate 
    assert (PIPELINE_ZEROINDEX(pipeline_index) = '0') or (PIPELINE_ZEROINDEX(pipeline_index) = '1') severity failure;
  end generate;

  loop_chunks: for chunk_index in 0 to SIZE-1 generate
    -- Organizing std_logic_vector into array for input.
    stage_indata(0)(chunk_index) <= a_data((chunk_index+1)*SHIFT_INCREMENT-1 downto chunk_index*SHIFT_INCREMENT);
    stage_shift(0) <= a_shift;
    -- Organizing array into std_logic_vector into array for output.
    b_data((chunk_index+1)*SHIFT_INCREMENT-1 downto chunk_index*SHIFT_INCREMENT) <= stage_outdata(N_STAGES-1)(chunk_index);
  end generate;

  loop_stages: for stage_index in 0 to N_STAGES-1 generate
    -- Just make a wide version of stage_indata with each chunk present twice
    -- so that the logic for barrel shifting doesn't have to consider the wrap.
    stage_inwidedata(stage_index)(SIZE-1 downto 0) <= stage_indata(stage_index);
    stage_inwidedata(stage_index)(2*SIZE-1 downto SIZE) <= stage_indata(stage_index);
    loop_chunks_in_stage: for chunk_index in 0 to SIZE-1 generate
      stage_outdata(stage_index)(chunk_index) <=
        stage_inwidedata(stage_index)(chunk_index + 2**stage_index) when stage_shift(stage_index)(stage_index) = '1' else
        stage_inwidedata(stage_index)(chunk_index);
    end generate;
  end generate;

  -- Deal with optional registers.
  yes_first_register: if PIPELINE_ZEROINDEX(0) /= '0' generate
    process(clk)
    begin
      if rising_edge(clk) then
        a_data <= i_data;
        a_shift <= i_shift;
      end if;
    end process;
  end generate;
  no_first_register: if PIPELINE_ZEROINDEX(0) = '0' generate
    a_data <= i_data;
    a_shift <= i_shift;
  end generate;

  loop_internal_registers: for stage_index in 0 to N_STAGES-2 generate 
    yes_register: if PIPELINE_ZEROINDEX(stage_index+1) /= '0' generate
      process(clk)
      begin
        if rising_edge(clk) then
          stage_indata(stage_index+1) <= stage_outdata(stage_index);
          stage_shift(stage_index+1) <= stage_shift(stage_index);
        end if;
      end process;
    end generate;
    no_register: if PIPELINE_ZEROINDEX(stage_index+1) = '0' generate
      stage_indata(stage_index+1) <= stage_outdata(stage_index);
      stage_shift(stage_index+1) <= stage_shift(stage_index);
    end generate;
  end generate;

  yes_last_register: if PIPELINE_ZEROINDEX(N_STAGES) /= '0' generate
    process(clk)
    begin
      if rising_edge(clk) then
        o_data <= b_data;
      end if;
    end process;
  end generate;
  no_last_register: if PIPELINE_ZEROINDEX(N_STAGES) = '0' generate
    o_data <= b_data;
  end generate;

end architecture;
