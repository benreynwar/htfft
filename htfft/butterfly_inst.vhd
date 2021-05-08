library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Just an example instantiation to run through tools to check
-- timing an resource utilization.

entity butterfly_inst is
  port (
    clk: in std_logic;
    i_a: in std_logic_vector(16-1 downto 0);
    i_b: in std_logic_vector(16-1 downto 0);
    i_t: in std_logic_vector(16-1 downto 0);
    o_c: out std_logic_vector(16+2-1 downto 0);
    o_d: out std_logic_vector(16+2-1 downto 0)
  );
end entity;

architecture arch of butterfly_inst is
begin
  bf: entity work.butterfly
    generic map (
      WIDTH => 16,
      TWIDDLE_WIDTH => 16,
      MULT_PIPELINE_LENGTH => 3,
      REG_I_P => true,
      REG_Q_R => true,
      REG_R_S => true,
      REG_S_O => true
      )
    port map (
      clk => clk,
      i_a => i_a,
      i_b => i_b,
      i_t => i_t,
      o_c => o_c,
      o_d => o_d
      );
end architecture;
