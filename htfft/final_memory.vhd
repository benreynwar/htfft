library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.htfft_pkg.all;

entity final_memory is
  generic (
    -- The number of bits used for each complex sample.
    WIDTH: positive;
    -- Number of samples processed per clock cycle.
    SPCC: positive;
    -- The number of samples in an FFT.
    N: positive
    );
  port (
    clk: in std_logic;
    i_beforefirst: in std_logic;
    i_data_a: in std_logic_vector(WIDTH*SPCC/2-1 downto 0);
    i_data_b: in std_logic_vector(WIDTH*SPCC/2-1 downto 0);
    o_beforefirst: out std_logic;
    o_data: out std_logic_vector(WIDTH*SPCC-1 downto 0)
    );
end entity;

architecture arch of final_memory is

  signal i_index: unsigned(logceil(N/SPCC)-1 downto 0);
  signal i_write_address_1: unsigned(logceil(N/SPCC)-1 downto 0);
  signal i_write_address_2: unsigned(logceil(N/SPCC)-1 downto 0);
  signal i_swap: std_logic;
  signal i_data_1: std_logic_vector(WIDTH*SPCC/2-1 downto 0);
  signal i_data_2: std_logic_vector(WIDTH*SPCC/2-1 downto 0);

  signal toread_index: unsigned(logceil(N/SPCC)-1 downto 0);

  signal fromread_new: std_logic;
  signal fromread_data_1: std_logic_vector(WIDTH*SPCC/2-1 downto 0);
  signal fromread_memdata_2: std_logic_vector(WIDTH*SPCC/2-1 downto 0);
  signal fromread_writtendata_2: std_logic_vector(WIDTH*SPCC/2-1 downto 0);
  signal fromread_data_2: std_logic_vector(WIDTH*SPCC/2-1 downto 0);
  signal fromread_swap: std_logic;
  signal fromread_beforefirst: std_logic;

  signal s_running: std_logic;

begin

  process(clk)
  begin
    if rising_edge(clk) then
      fromread_new <= '0';
      if (i_index = N/SPCC/2-1) then
        toread_index <= (others => '0');
        fromread_beforefirst <= '1';
      else
        toread_index <= toread_index + 1;
        fromread_beforefirst <= '0';
      end if;
      if (i_index = N/SPCC-1) then
        s_running <= '0';
        fromread_new <= '1';
      end if;
      fromread_swap <= toread_index(logceil(N/SPCC)-1);
      if i_beforefirst = '1' then
        i_index <= (others => '0');
        s_running <= '1';
      elsif s_running = '1' then
        i_index <= i_index + 1;
      end if;
    end if;
  end process;


  i_write_address_1 <= i_index/2 when i_index(0) = '0' else
                       i_index/2 + N/SPCC/2;
  i_write_address_2 <= i_index/2 + N/SPCC/2 when i_index(0) = '0' else
                       i_index/2;
  i_swap <= i_index(0); 
  i_data_1 <= i_data_a when i_swap = '0' else
              i_data_b;
  i_data_2 <= i_data_b when i_swap = '0' else
              i_data_a;


  memory_1: entity work.memory
  generic map (
    WIDTH => SPCC*WIDTH/2,
    DEPTH => N/SPCC,
    ADDRESS_CLASH => "OLD"
    )
  port map (
    clk => clk,
    write_valid => '1',
    write_address => i_write_address_1,
    write_data => i_data_1,
    toread_valid => '1',
    toread_address => toread_index,
    fromread_data => fromread_data_1
    );

  memory_2: entity work.memory
  generic map (
    WIDTH => SPCC*WIDTH/2,
    DEPTH => N/SPCC,
    ADDRESS_CLASH => "OLD"
    )
  port map (
    clk => clk,
    write_valid => '1',
    write_address => i_write_address_2,
    write_data => i_data_2,
    toread_valid => '1',
    toread_address => toread_index,
    fromread_data => fromread_memdata_2
    );
  -- There's one piece of data where we need to skip the
  -- memory for 
  process(clk)
  begin
    if rising_edge(clk) then
      fromread_writtendata_2 <= i_data_2;
    end if;
  end process;
  fromread_data_2 <= fromread_writtendata_2 when (fromread_new = '1') else
                     fromread_memdata_2;

  o_beforefirst <= fromread_beforefirst;
  o_data(SPCC*WIDTH/2-1 downto 0) <= fromread_data_1 when fromread_swap = '0' else
                                     fromread_data_2;
  o_data(SPCC*WIDTH-1 downto SPCC*WIDTH/2) <= fromread_data_2 when fromread_swap = '0' else
                                              fromread_data_1;

end architecture;
