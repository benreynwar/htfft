library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.htfft_pkg.all;

entity stage_{{n}}{{suffix}} is
  port (
    clk: in std_logic;
    -- The reset is just to get the addresses in sync with the
    -- data flow.  If it arrives on the clock cycle immediately
    -- before a new vector starts it will have no effect since
    -- the addresses would be getting initialized anyway.
    i_reset: in std_logic;
    i_data_a: in std_logic_vector({{width}}*{{size}}/2-1 downto 0);
    i_data_b: in std_logic_vector({{width}}*{{size}}/2-1 downto 0);
    o_reset: out std_logic;
    o_data_a: out std_logic_vector(({{width}}+2)*{{size}}/2-1 downto 0);
    o_data_b: out std_logic_vector(({{width}}+2)*{{size}}/2-1 downto 0)
  );
end entity;

architecture arch of stage_{{n}}{{suffix}} is
  constant N: positive := {{n}};
  constant WIDTH: positive := {{width}};
  constant TWIDDLE_WIDTH: positive := {{twiddle_width}};
  constant SIZE: positive := {{size}};
  constant OUTPUT_WIDTH: positive := WIDTH + 2;
  constant L: positive := N/SIZE;

  function ADDRESS_CLASH return string is
  begin
    if L=2 then
      -- For L=2 we get address clash so we need to make sure our
      -- memory can handle this.
      return "OLD";
    else
      -- For larger N we'll never get an address clash so we can
      -- make sure memory isn't constrained to support this.
      return "UNDEFINED";
    end if;
  end function;

  signal write_index: unsigned(logceil(L)-1 downto 0);
  signal write_address_a: unsigned(logceil(L)-1 downto 0);
  signal write_address_b: unsigned(logceil(L)-1 downto 0);
  signal write_data_a: std_logic_vector(SIZE*WIDTH/2-1 downto 0);
  signal write_data_b: std_logic_vector(SIZE*WIDTH/2-1 downto 0);

  signal read_index: unsigned(logceil(L)-1 downto 0);

  signal toread_address_a: unsigned(logceil(L)-1 downto 0);
  signal toread_address_b: unsigned(logceil(L)-1 downto 0);

  signal fromread_data_a: std_logic_vector(SIZE*WIDTH/2-1 downto 0);
  signal fromread_data_b: std_logic_vector(SIZE*WIDTH/2-1 downto 0);

  signal tobutterfly_swap: std_logic;
  signal tobutterfly_data_a: std_logic_vector(SIZE*WIDTH/2-1 downto 0);
  signal tobutterfly_data_b: std_logic_vector(SIZE*WIDTH/2-1 downto 0);

  subtype t_twiddle is std_logic_vector(TWIDDLE_WIDTH-1 downto 0);
  type array_of_twiddles is array(natural range <>) of t_twiddle;
  subtype t_batch_of_twiddles is array_of_twiddles(SIZE/2-1 downto 0);
  type array_of_batches_of_twiddles is array(natural range <>) of t_batch_of_twiddles;

  subtype t_data is std_logic_vector(WIDTH-1 downto 0);
  type array_of_data is array(natural range <>) of t_data;
  signal tobutterfly_dataarray_a: array_of_data(SIZE/2-1 downto 0);
  signal tobutterfly_dataarray_b: array_of_data(SIZE/2-1 downto 0);
  signal tobutterfly_twiddles: array_of_twiddles(SIZE/2-1 downto 0);

  subtype t_odata is std_logic_vector(WIDTH+2-1 downto 0);
  type array_of_odata is array(natural range <>) of t_odata;
  signal o_dataarray_a: array_of_odata(SIZE/2-1 downto 0);
  signal o_dataarray_b: array_of_odata(SIZE/2-1 downto 0);

  constant LOCAL_TWIDDLES: array_of_batches_of_twiddles(N/SIZE-1 downto 0) := ({% for twiddle_batch in twiddle_batches %}
    {{loop.index0}} => ({% for twiddle in twiddle_batch %}
       {{loop.index0}} => "{{twiddle}}"{% if not loop.last %},{% endif %}{% endfor %}
       ){% if not loop.last %},{% endif %}{% endfor %}
  );


  constant BUTTERFLY_PIPELINE_LENGTH: positive := 7;

  signal i_reset_slv: std_logic_vector(0 downto 0);
  signal o_reset_slv: std_logic_vector(0 downto 0);

begin

  process(clk)
  begin
    if rising_edge(clk) then
      if write_index = L/2 then
        -- We've writing the second half of the data needed for the
        -- first read of the next stage so we can do that first read
        -- next clock cycle.
        read_index <= (others => '0');
      else
        read_index <= read_index + 1;
      end if;
      if write_index = L-1 then
        write_index <= (others => '0');
      else
        write_index <= write_index + 1;
      end if;
      if i_reset = '1' then
        write_index <= (others => '0');
      end if;
    end if;
  end process;

  -- We're splitting the data into two memories.  This is so that we can write
  -- into the two regions we need to, and read from the two regions we need to
  -- every clock cycle.
  -- The address mappings are just chosen so that the two reads are always one
  -- in each memory, and the same for the two writes.

  -- FIXME: I think we could probably halve the memory use here, but let's get
  -- it working first.  We start reading after writing half of the contents and
  -- we should be able to use the addresses we've just read to write into.
  write_address_a <= write_index;
  write_address_b <= write_index;
  toread_address_a <= read_index;
  toread_address_b(logceil(L)-1) <= not read_index(logceil(L)-1);
  toread_address_b(logceil(L)-1-1 downto 0) <= read_index(logceil(L)-1-1 downto 0);

  write_data_a <= i_data_a when write_index(logceil(L)-1) = '0' else
                  i_data_b;
  write_data_b <= i_data_b when write_index(logceil(L)-1) = '0' else
                  i_data_a;

  memory_a: entity work.memory
    generic map (
      DEPTH => L,
      WIDTH => SIZE*WIDTH/2,
      ADDRESS_CLASH => ADDRESS_CLASH
      )
    port map (
      clk => clk,
      toread_valid => '1',
      toread_address => toread_address_a,
      fromread_data => fromread_data_a,
      write_valid => '1',
      write_address => write_address_a,
      write_data => write_data_a
      );

  memory_b: entity work.memory
    generic map (
      DEPTH => L,
      WIDTH => SIZE*WIDTH/2,
      ADDRESS_CLASH => ADDRESS_CLASH
      )
    port map (
      clk => clk,
      toread_valid => '1',
      toread_address => toread_address_b,
      fromread_data => fromread_data_b,
      write_valid => '1',
      write_address => write_address_b,
      write_data => write_data_b
      );

  tobutterfly_data_a <= fromread_data_a when tobutterfly_swap = '0' else
                        fromread_data_b;
  tobutterfly_data_b <= fromread_data_b when tobutterfly_swap = '0' else
                        fromread_data_a;

  process(clk)
  begin
    if rising_edge(clk) then
      tobutterfly_twiddles <= LOCAL_TWIDDLES(to_integer(read_index));
      tobutterfly_swap <= write_index(logceil(L)-1);
    end if;
  end process;

  loop_butterflys: for bf_index in 0 to SIZE/2-1 generate
    tobutterfly_dataarray_a(bf_index) <= tobutterfly_data_a((bf_index+1)*WIDTH-1 downto bf_index*WIDTH);
    tobutterfly_dataarray_b(bf_index) <= tobutterfly_data_b((bf_index+1)*WIDTH-1 downto bf_index*WIDTH);
    bf: entity work.butterfly
      generic map (
        WIDTH => WIDTH,
        TWIDDLE_WIDTH => TWIDDLE_WIDTH,
        MULT_PIPELINE_LENGTH => 3,
        REG_I_P => true,
        REG_Q_R => true,
        REG_R_S => true,
        REG_S_O => true
      )
      port map (
        clk => clk,
        i_a => tobutterfly_dataarray_a(bf_index),
        i_b => tobutterfly_dataarray_b(bf_index),
        i_t => tobutterfly_twiddles(bf_index),
        o_c => o_dataarray_a(bf_index),
        o_d => o_dataarray_b(bf_index)
        );
    o_data_a((bf_index+1)*OUTPUT_WIDTH-1 downto bf_index*OUTPUT_WIDTH) <=
      std_logic_vector(o_dataarray_a(bf_index));
    o_data_b((bf_index+1)*OUTPUT_WIDTH-1 downto bf_index*OUTPUT_WIDTH) <=
      std_logic_vector(o_dataarray_b(bf_index));
  end generate;

  i_reset_slv(0) <= i_reset;
  sr: entity work.shift_register
    generic map (
      WIDTH => 1,
      LENGTH => BUTTERFLY_PIPELINE_LENGTH + 1 + N/2
      )
    port map (
      clk => clk,
      i_data => i_reset_slv,
      o_data => o_reset_slv
      );
  o_reset <= o_reset_slv(0);
  
end architecture;
