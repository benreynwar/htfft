library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.htfft_pkg.all;

entity initial_memory is
  generic (
    -- The number of bits used for each complex sample.
    WIDTH: positive;
    -- Number of samples processed per clock cycle.
    SPCC: positive;
    -- The number of samples in an FFT.
    N: positive;
    -- The pipeline used in the barrel shifter.
    BARREL_SHIFTER_PIPELINE: string
    );
  port (
    clk: in std_logic;
    i_reset: in std_logic;
    i_data: in std_logic_vector(WIDTH*SPCC-1 downto 0);
    o_data: out std_logic_vector(WIDTH*SPCC-1 downto 0)
    );

end entity;

architecture arch of initial_memory is
  signal i_addressreversed: std_logic;
  signal i_address: unsigned(logceil(N/SPCC)-1 downto 0);
  signal i_shift: unsigned(logceil(SPCC)-1 downto 0);
  subtype t_longaddress is unsigned(logceil(N)-1 downto 0);
  type array_of_longaddress is array(natural range <>) of t_longaddress;
  signal i_longaddresses: array_of_longaddress(SPCC-1 downto 0);
  signal i_reversedlongaddresses: array_of_longaddress(SPCC-1 downto 0);

begin

  loop_samples: for sample_index in 0 to SPCC-1 generate
    i_longaddresses(sample_index)(logceil(N)-1 downto logceil(SPCC)) <= i_address;
    i_longaddresses(sample_index)(logceil(SPCC)-1 downto 0) <= to_unsigned(sample_index, logceil(SPCC));
    loop_bits: for bit_index in 0 to logceil(N)-1 generate
      i_reversedlongaddresses(sample_index)(bit_index) <= i_longaddressees(sample_index)(logceil(N)-1-bit_index);
    end generate;
  end generate;
  i_usedaddresses <= i_longaddresess when i_addressreversed = '0' else
                     i_reversedlongaddresses;

  -- This condition is necessary for the barrel shifting into the
  -- memories to work correctly.
  assert logceil(SPCC)*2 < logceil(N) severity failure;

  process(clk)
  begin
    if rising_edge(clk) then
      if i_address = N/SPCC-1 then
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

  upper_bits: for bit_index in logceil(SPCC) generate
    i_shift(bit_index) <= i_address(logceil(N/SPCC)-1-bit_index) when i_addressreversed = '0' else
                          i_address(bit_index);
  end generate;

  preshifter: entity work.barrel_shifter
    generic map (
      SHIFT_INCREMENT => WIDTH,
      SIZE => SPCC,
      PIPELINE => BARREL_SHIFTER_PIPELINE
      )
    port map (
      clk => clk,
      i_shift => i_shift,
      i_data => i_data,
      o_data => a_data
      );

  pre_sr: entity work.shift_register
    generic map (
      WIDTH => logceil(N/SPCC),
      LENGTH => BARREL_SHIFTER_PIPELINE_LENGTH
      )
    port map (
      clk => clk,
      i_data => i_address_slv,
      o_data => a_address_slv
      );

  loop_memories: for memory_index in 0 to SPCC-1 generate
    mem: entity work.memory
      generic map (
        WIDTH => WIDTH,
        DEPTH => N/SPCC
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
      SIZE => SPCC
      )
    port map (
      clk => clk,
      i_shift => b_shift,
      i_data => b_data,
      o_data => o_data
      );
      
end architecture;
