library ieee;
use ieee.std_logic_1164.all;

entity initial_memory is
  generic (
    WIDTH: positive;
    SIZE: positive;
    N: positive
    );
  port (
    clk: in std_logic;
    i_reset: in std_logic;
    i_data: in std_logic_vector(WIDTH*SIZE-1 downto 0);
    o_data: out std_logic_vector(WIDTH*SIZE-1 downto 0);
    );

end entity;

architecture arch of initial_memory is
  signal i_addressreversed: std_logic;
  signal i_address: unsigned(logceil(N/SIZE)-1 downto 0);
  signal i_shift: unsigned(logceil(SIZE)-1 downto 0);
begin


  process(clk)
  begin
    if rising_edge(clk) then
      if i_address = N/SIZE-1 then
        i_address <= (others => '0');
        i_addressreversed <= not i_addressreversed;
      else
        i_address <= i_address + 1;
      end if;
      if i_reset = '1' then
        i_address <= (others => '0');
        i_addressreversed <= not i_addressreversed;
      end if;
    end if;
  end process;

  upper_bits: for bit_index in logceil(SIZE) generate
    i_shift(bit_index) <= i_address(logceil(N/SIZE)-1-bit_index) when i_addressreversed = '0' else
                          i_address(bit_index);
  end generate;

  preshifter: entity work.barrel_shifter
    generic map (
      WIDTH => WIDTH,
      SIZE => SIZE
      )
    port map (
      clk => clk,
      i_shift => i_shift,
      i_data => i_data,
      o_data => a_data
      );

  pre_sr: entity work.shift_register
    generic map (
      WIDTH => logceil(N/SIZE),
      LENGTH => BARREL_SHIFTER_PIPELINE_LENGTH
      )
    port map (
      clk => clk,
      i_data => i_address_slv,
      o_data => a_address_slv
      );

  loop_memories: for memory_index in 0 to SIZE generate
    mem: entity work.memory
      generic map (
        WIDTH => WIDTH,
        DEPTH => N/SIZE
        )
      port map (
        clk => clk,
        write_valid => '1',
        write_address => write_addresses(memory_index),
        write_data => write_datas(memory_index),
        toread_valid => '1',
        toread_address => read_addresses(memory_index),
        fromread_data => read_data(memory_index)
        );
  end generate;

  postshifter: entity work.barrel_shifter
    generic map (
      WIDTH => WIDTH,
      SIZE => SIZE
      )
    port map (
      clk => clk,
      i_shift => b_shift,
      i_data => b_data,
      o_data => o_data
      );
      
end architecture;
