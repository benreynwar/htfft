library ieee;
use ieee.std_logic_1164.all;

entity unrolled_fft{{suffix}} is
  port (
    clk: in std_logic;
    i_data: in std_logic_vector({{input_width}}*{{size}}-1 downto 0);
    o_data: out std_logic_vector(({{input_width}}+2*{{logceil_size}})*{{size}}-1 downto 0)
    );
end entity;

architecture arch of unrolled_fft{{suffix}} is
  constant INPUT_WIDTH: positive := {{input_width}};
  constant OUTPUT_WIDTH: positive := INPUT_WIDTH + 2*{{logceil_size}};
  constant SIZE: positive := {{size}};
  signal i_reordereddata: std_logic_vector(INPUT_WIDTH*SIZE-1 downto 0);
begin

  reordering: entity work.comb_reordering
    generic map (
      WIDTH => INPUT_WIDTH,
      SIZE => SIZE
      )
    port map (
      i_data => i_data,
      o_data => i_reordereddata
      );

  innner: entity work.unrolled_fft_inner_{{size}}{{suffix}}
    port map (
      clk => clk,
      i_data => i_reordereddata,
      o_data => o_data
      );

end architecture;
