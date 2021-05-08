library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity mult is
  generic (
    A_WIDTH: positive;
    B_WIDTH: positive;
    PIPELINE_LENGTH: natural
    );
  port (
    clk: in std_logic;
    i_a: in signed(A_WIDTH-1 downto 0);
    i_b: in signed(B_WIDTH-1 downto 0);
    o_c: out signed(A_WIDTH+B_WIDTH-1 downto 0)
  );
end entity;

architecture arch of mult is
  subtype t_data is signed(A_WIDTH+B_WIDTH-1 downto 0);
  type array_of_data is array(natural range <>) of t_data;
  signal dataarray: array_of_data(PIPELINE_LENGTH-1 downto 0);
  signal multed: t_data;
  -- For now forcing use of the DSP.
  -- FIXME: For small width it probably makes sense to use LUTs instead.
  -- Perhaps it's best to let Vivado decide this itself, but because
  -- I'm unfamiliar with DSP I'm forcing it to use it for now so I
  -- can get a feel for it.
  attribute use_dsp: string;
  attribute use_dsp of multed : signal is "yes";
begin
  multed <= i_a * i_b;
  zero_length: if PIPELINE_LENGTH = 0 generate
    o_c <= multed;
  end generate;
  non_zero_length: if PIPELINE_LENGTH > 0 generate
    -- Hopefully tools can infer a pipelined multiplier
    -- from this.  (Seems like Vivado can).
    process(clk)
    begin
      if rising_edge(clk) then
        dataarray(PIPELINE_LENGTH-1) <= multed;
        for ii in 0 to PIPELINE_LENGTH-2 loop
          dataarray(ii) <= dataarray(ii+1);
        end loop;
      end if;
    end process;
    o_c <= dataarray(0);
  end generate;
end architecture;
