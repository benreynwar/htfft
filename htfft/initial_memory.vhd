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
    reset: in std_logic;
    i_beforefirst: in std_logic;
    i_data: in std_logic_vector(WIDTH*SPCC-1 downto 0);
    o_data: out std_logic_vector(WIDTH*SPCC-1 downto 0)
    );

end entity;

architecture arch of initial_memory is
  signal i_addressreversed: std_logic;
  signal i_address: unsigned(logceil(N/SPCC)-1 downto 0);
  constant ADDRESS_WIDTH: positive := logceil(N/SPCC);
  signal i_address_shift_reversed: std_logic_vector(logceil(SPCC)+logceil(N/SPCC)+1-1 downto 0);
  signal i_shift: unsigned(logceil(SPCC)-1 downto 0);
  signal i_shift_rev: unsigned(logceil(SPCC)-1 downto 0);
  signal i_shift_slv: std_logic_vector(logceil(SPCC)-1 downto 0);
  subtype t_longaddress is unsigned(logceil(N)-1 downto 0);
  type array_of_longaddress is array(natural range <>) of t_longaddress;
  signal i_longaddresses: array_of_longaddress(SPCC-1 downto 0);
  signal i_reversedlongaddresses: array_of_longaddress(SPCC-1 downto 0);
  signal i_usedaddresses: array_of_longaddress(SPCC-1 downto 0);
  subtype t_inmemaddress is unsigned(logceil(N/SPCC)-1 downto 0);
  type array_of_inmemaddress is array(natural range <>) of t_inmemaddress;
  signal i_inmemaddresses: array_of_inmemaddress(SPCC-1 downto 0);
  --signal a_addressreversed: std_logic;
  --signal a_address_shift_reversed: std_logic_vector(logceil(SPCC)+logceil(N/SPCC)+1-1 downto 0);
  --signal a_address: unsigned(logceil(N/SPCC)-1 downto 0);
  signal i_dataandaddresses: std_logic_vector((WIDTH+ADDRESS_WIDTH)*SPCC-1 downto 0);
  signal a_dataandaddresses: std_logic_vector((WIDTH+ADDRESS_WIDTH)*SPCC-1 downto 0);
  signal a_inmemaddresses: array_of_inmemaddress(SPCC-1 downto 0);
  subtype t_data is std_logic_vector(WIDTH-1 downto 0);
  type array_of_data is array(natural range <>) of t_data;
  signal a_datas: array_of_data(SPCC-1 downto 0);
  signal a_shift: unsigned(logceil(SPCC)-1 downto 0);
  signal a_shift_slv: std_logic_vector(logceil(SPCC)-1 downto 0);
  signal b_shift: unsigned(logceil(SPCC)-1 downto 0);
  signal b_datas: array_of_data(SPCC-1 downto 0);
  signal b_data: std_logic_vector(WIDTH*SPCC-1 downto 0);

  constant BARREL_SHIFTER_PIPELINE_LENGTH: natural := count_pipeline_length(
    BARREL_SHIFTER_PIPELINE);

begin

  loop_samples: for sample_index in 0 to SPCC-1 generate
    i_longaddresses(sample_index)(logceil(N)-1 downto logceil(SPCC)) <= i_address;
    i_longaddresses(sample_index)(logceil(SPCC)-1 downto 0) <= to_unsigned(sample_index, logceil(SPCC));
    loop_bits: for bit_index in 0 to logceil(N)-1 generate
      i_reversedlongaddresses(sample_index)(bit_index) <=
        i_longaddresses(sample_index)(logceil(N)-1-bit_index);
    end generate;
    i_inmemaddresses(sample_index) <= i_usedaddresses(sample_index)(logceil(N)-1 downto logceil(SPCC));
    i_dataandaddresses(sample_index*(WIDTH+ADDRESS_WIDTH)+WIDTH-1 downto
                       sample_index*(WIDTH+ADDRESS_WIDTH)) <=
      i_data((sample_index+1)*WIDTH-1 downto sample_index*WIDTH);
    i_dataandaddresses((sample_index+1)*(WIDTH+ADDRESS_WIDTH)-1 downto
                       sample_index*(WIDTH+ADDRESS_WIDTH)+WIDTH) <=
      std_logic_vector(i_inmemaddresses(sample_index));
    a_datas(sample_index) <=
      a_dataandaddresses(sample_index*(WIDTH+ADDRESS_WIDTH)+WIDTH-1 downto
                         sample_index*(WIDTH+ADDRESS_WIDTH));
    a_inmemaddresses(sample_index) <=
      unsigned(a_dataandaddresses((sample_index+1)*(WIDTH+ADDRESS_WIDTH)-1 downto
                                  sample_index*(WIDTH+ADDRESS_WIDTH)+WIDTH));
    b_data((sample_index+1)*WIDTH-1 downto sample_index*WIDTH) <= b_datas(sample_index);
  end generate;
  i_usedaddresses <= i_longaddresses when i_addressreversed = '0' else
                     i_reversedlongaddresses;

  -- This condition is necessary for the barrel shifting into the
  -- memories to work correctly.
  assert logceil(SPCC)*2 <= logceil(N) severity failure;

  process(clk)
  begin
    if rising_edge(clk) then
      if i_address = N/SPCC-1 then
        i_address <= (others => '0');
        i_addressreversed <= not i_addressreversed;
      else
        i_address <= i_address + 1;
      end if;
      if i_beforefirst = '1' then
        i_address <= (others => '0');
        i_addressreversed <= not i_addressreversed;
      end if;
      if reset = '1' then
        i_addressreversed <= '1';
      end if;
    end if;
  end process;

  upper_bits: for bit_index in 0 to logceil(SPCC)-1 generate
    i_shift_rev(bit_index) <= i_address(logceil(N/SPCC)-1-bit_index);
  end generate;
  i_shift <= (others => '0') when i_shift_rev = 0 else
             SPCC-i_shift_rev;

  preshifter: entity work.barrel_shifter
    generic map (
      SHIFT_INCREMENT => WIDTH+ADDRESS_WIDTH,
      SIZE => SPCC,
      PIPELINE => BARREL_SHIFTER_PIPELINE
      )
    port map (
      clk => clk,
      i_shift => i_shift,
      i_data => i_dataandaddresses,
      o_data => a_dataandaddresses
      );

  i_shift_slv <= std_logic_vector(i_shift);
  pre_sr: entity work.shift_register
    generic map (
      WIDTH => logceil(SPCC),
      LENGTH => BARREL_SHIFTER_PIPELINE_LENGTH
      )
    port map (
      clk => clk,
      i_data => i_shift_slv,
      o_data => a_shift_slv
      );
  a_shift <= unsigned(a_shift_slv);

  loop_memories: for memory_index in 0 to SPCC-1 generate
    mem: entity work.memory
      generic map (
        WIDTH => WIDTH,
        DEPTH => N/SPCC,
        ADDRESS_CLASH => "OLD"
        )
      port map (
        clk => clk,
        write_valid => '1',
        write_address => a_inmemaddresses(memory_index),
        write_data => a_datas(memory_index),
        toread_valid => '1',
        toread_address => a_inmemaddresses(memory_index),
        fromread_data => b_datas(memory_index)
        );
  end generate;

  process(clk)
  begin
    if rising_edge(clk) then
      if a_shift = 0 then
        b_shift <= (others => '0');
      else
        b_shift <= SPCC-a_shift;
      end if;
    end if;
  end process;

  postshifter: entity work.barrel_shifter
    generic map (
      SHIFT_INCREMENT => WIDTH,
      SIZE => SPCC,
      PIPELINE => BARREL_SHIFTER_PIPELINE
      )
    port map (
      clk => clk,
      i_shift => b_shift,
      i_data => b_data,
      o_data => o_data
      );
      
end architecture;
