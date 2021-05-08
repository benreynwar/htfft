library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity butterfly is
  generic (
    WIDTH: positive;
    TWIDDLE_WIDTH: positive;
    MULT_PIPELINE_LENGTH: natural;
    REG_I_P: boolean;
    REG_Q_R: boolean;
    REG_R_S: boolean;
    REG_S_O: boolean
    );
  port (
    clk: in std_logic;
    i_a: in std_logic_vector(WIDTH-1 downto 0);
    i_b: in std_logic_vector(WIDTH-1 downto 0);
    i_t: in std_logic_vector(TWIDDLE_WIDTH-1 downto 0);
    o_c: out std_logic_vector(WIDTH+2-1 downto 0);
    o_d: out std_logic_vector(WIDTH+2-1 downto 0)
  );
end entity;

architecture arch of butterfly is

  function bool_to_int(value: boolean) return integer is 
  begin
    if value then
      return 1;
    else
      return 0;
    end if;
  end function;
    

  constant PIPELINE_LENGTH_TO_S: natural := bool_to_int(REG_I_P) + bool_to_int(REG_Q_R) + bool_to_int(REG_R_S) +
                                            MULT_PIPELINE_LENGTH;

  signal p_b: std_logic_vector(WIDTH-1 downto 0);
  signal p_t: std_logic_vector(TWIDDLE_WIDTH-1 downto 0);
  signal p_b_real: signed(WIDTH/2-1 downto 0);
  signal p_b_imag: signed(WIDTH/2-1 downto 0);
  signal p_t_real: signed(TWIDDLE_WIDTH/2-1 downto 0);
  signal p_t_imag: signed(TWIDDLE_WIDTH/2-1 downto 0);

  signal q_bt_real_real_expanded: signed(WIDTH/2+TWIDDLE_WIDTH/2-1 downto 0);
  signal q_bt_real_imag_expanded: signed(WIDTH/2+TWIDDLE_WIDTH/2-1 downto 0);
  signal q_bt_imag_real_expanded: signed(WIDTH/2+TWIDDLE_WIDTH/2-1 downto 0);
  signal q_bt_imag_imag_expanded: signed(WIDTH/2+TWIDDLE_WIDTH/2-1 downto 0);
  signal q_bt_real_real: signed(WIDTH/2-1 downto 0);
  signal q_bt_real_imag: signed(WIDTH/2-1 downto 0);
  signal q_bt_imag_real: signed(WIDTH/2-1 downto 0);
  signal q_bt_imag_imag: signed(WIDTH/2-1 downto 0);

  signal r_bt_real_real: signed(WIDTH/2-1 downto 0);
  signal r_bt_real_imag: signed(WIDTH/2-1 downto 0);
  signal r_bt_imag_real: signed(WIDTH/2-1 downto 0);
  signal r_bt_imag_imag: signed(WIDTH/2-1 downto 0);
  signal r_bt_real: signed(WIDTH/2-1 downto 0);
  signal r_bt_imag: signed(WIDTH/2-1 downto 0);

  signal s_bt_real: signed(WIDTH/2-1 downto 0);
  signal s_bt_imag: signed(WIDTH/2-1 downto 0);
  signal s_a: std_logic_vector(WIDTH-1 downto 0);
  signal s_a_real: signed(WIDTH/2-1 downto 0);
  signal s_a_imag: signed(WIDTH/2-1 downto 0);
  signal s_c_real: signed(WIDTH/2+1-1 downto 0);
  signal s_c_imag: signed(WIDTH/2+1-1 downto 0);
  signal s_d_real: signed(WIDTH/2+1-1 downto 0);
  signal s_d_imag: signed(WIDTH/2+1-1 downto 0);
  signal s_c: std_logic_vector(WIDTH+2-1 downto 0);
  signal s_d: std_logic_vector(WIDTH+2-1 downto 0);
begin

  yes_reg_i_p: if REG_I_P generate
    process(clk)
    begin
      if rising_edge(clk) then
        p_b <= i_b;
        p_t <= i_t;
      end if;
    end process;
  end generate;
  no_reg_i_p: if not REG_I_P generate
    p_b <= i_b;
    p_t <= i_t;
  end generate;

  p_b_real <= signed(p_b(WIDTH-1 downto WIDTH/2));
  p_b_imag <= signed(p_b(WIDTH/2-1 downto 0));
  p_t_real <= signed(p_t(TWIDDLE_WIDTH-1 downto TWIDDLE_WIDTH/2));
  p_t_imag <= signed(p_t(TWIDDLE_WIDTH/2-1 downto 0));
    
  real_real_mult: entity work.mult
    generic map (
      A_WIDTH => WIDTH/2,
      B_WIDTH => TWIDDLE_WIDTH/2,
      PIPELINE_LENGTH => MULT_PIPELINE_LENGTH
      )
    port map (
      clk => clk,
      i_a => p_b_real,
      i_b => p_t_real,
      o_c => q_bt_real_real_expanded
      );
  real_imag_mult: entity work.mult
    generic map (
      A_WIDTH => WIDTH/2,
      B_WIDTH => TWIDDLE_WIDTH/2,
      PIPELINE_LENGTH => MULT_PIPELINE_LENGTH
      )
    port map (
      clk => clk,
      i_a => p_b_real,
      i_b => p_t_imag,
      o_c => q_bt_real_imag_expanded
      );
  imag_real_mult: entity work.mult
    generic map (
      A_WIDTH => WIDTH/2,
      B_WIDTH => TWIDDLE_WIDTH/2,
      PIPELINE_LENGTH => MULT_PIPELINE_LENGTH
      )
    port map (
      clk => clk,
      i_a => p_b_imag,
      i_b => p_t_real,
      o_c => q_bt_imag_real_expanded
      );
  imag_imag_mult: entity work.mult
    generic map (
      A_WIDTH => WIDTH/2,
      B_WIDTH => TWIDDLE_WIDTH/2,
      PIPELINE_LENGTH => MULT_PIPELINE_LENGTH
      )
    port map (
      clk => clk,
      i_a => p_b_imag,
      i_b => p_t_imag,
      o_c => q_bt_imag_imag_expanded
      );
      
  -- Here we're truncating it directly downto WIDTH.
  -- FIXME: Might be better to keep afew more bits until after a few more additions.
  -- FIXME: Probably should do better rounding rather than just truncation as well.
  -- Uppermost bit of expanded can be ignored since it's the result of
  -- multiplying two signed numbers but we still added the widths together.
  q_bt_real_real <= q_bt_real_real_expanded(WIDTH/2+TWIDDLE_WIDTH/2-2-1 downto TWIDDLE_WIDTH/2-2);
  q_bt_real_imag <= q_bt_real_imag_expanded(WIDTH/2+TWIDDLE_WIDTH/2-2-1 downto TWIDDLE_WIDTH/2-2);
  q_bt_imag_real <= q_bt_imag_real_expanded(WIDTH/2+TWIDDLE_WIDTH/2-2-1 downto TWIDDLE_WIDTH/2-2);
  q_bt_imag_imag <= q_bt_imag_imag_expanded(WIDTH/2+TWIDDLE_WIDTH/2-2-1 downto TWIDDLE_WIDTH/2-2);

  yes_reg_q_r: if REG_Q_R generate
    process(clk)
    begin
      if rising_edge(clk) then
        r_bt_real_real <= q_bt_real_real;
        r_bt_real_imag <= q_bt_real_imag;
        r_bt_imag_real <= q_bt_imag_real;
        r_bt_imag_imag <= q_bt_imag_imag;
      end if;
    end process;
  end generate;
  no_reg_q_r: if not REG_Q_R generate
    r_bt_real_real <= q_bt_real_real;
    r_bt_real_imag <= q_bt_real_imag;
    r_bt_imag_real <= q_bt_imag_real;
    r_bt_imag_imag <= q_bt_imag_imag;
  end generate;

  -- We're assuming that i_a and i_b both have magnitude <= 1 so that these additions
  -- can't overflow even if we don't extend width. 
  r_bt_real <= r_bt_real_real - r_bt_imag_imag;
  r_bt_imag <= r_bt_real_imag + r_bt_imag_real;

  yes_reg_r_s: if REG_R_S generate
    process(clk)
    begin
      if rising_edge(clk) then
        s_bt_real <= r_bt_real;
        s_bt_imag <= r_bt_imag;
      end if;
    end process;
  end generate;
  no_reg_r_s: if not REG_R_S generate
    s_bt_real <= r_bt_real;
    s_bt_imag <= r_bt_imag;
  end generate;

  delay_a: entity work.shift_register
    generic map (
      WIDTH => WIDTH,
      LENGTH => PIPELINE_LENGTH_TO_S
      )
    port map (
      clk => clk,
      i_data => i_a,
      o_data => s_a
      );

  s_a_real <= signed(s_a(WIDTH-1 downto WIDTH/2));
  s_a_imag <= signed(s_a(WIDTH/2-1 downto 0));
  

  s_c_real <= resize(s_a_real, WIDTH/2+1) + resize(s_bt_real, WIDTH/2+1);
  s_c_imag <= resize(s_a_imag, WIDTH/2+1) + resize(s_bt_imag, WIDTH/2+1);
  s_c(WIDTH+2-1 downto WIDTH/2+1) <= std_logic_vector(s_c_real);
  s_c(WIDTH/2+1-1 downto 0) <= std_logic_vector(s_c_imag);
  s_d_real <= resize(s_a_real, WIDTH/2+1) - resize(s_bt_real, WIDTH/2+1);
  s_d_imag <= resize(s_a_imag, WIDTH/2+1) - resize(s_bt_imag, WIDTH/2+1);
  s_d(WIDTH+2-1 downto WIDTH/2+1) <= std_logic_vector(s_d_real);
  s_d(WIDTH/2+1-1 downto 0) <= std_logic_vector(s_d_imag);
  -- Q_O
  -- FIXME Output buffer

  yes_reg_s_o: if REG_S_O generate
    process(clk)
    begin
      if rising_edge(clk) then
        o_c <= s_c;
        o_d <= s_d;
      end if;
    end process;
  end generate;
  no_reg_s_o: if not REG_S_O generate
    o_c <= s_c;
    o_d <= s_d;
  end generate;

end architecture;
