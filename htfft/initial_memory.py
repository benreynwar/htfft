"""
Thinking about how to organize the initial memory that
data is stored in.
Because we want to access data in order of bit-reversed
address we need to a memory where we will store the
data until we need to start using it.

If we are processing SPCC samples per clock cycle then
we probably want to store each of those samples in a different
memory so that we can access them in a different order.

However we need to think a bit to make sure that when we
write each sample goes to a different memory, and when we
read each sample can come from a different memory.
"""

# Lets say the FFT has a given size N.
# And we want to process SPCC samples per clock cycle.
# So we take L clock cycles to consume the data from the FFT where
# L = N/SPCC

# We need SPCC memorys to store the samples.
# Each sample has an address from 0 to N-1.

# It seems to work if we take the upper logceil(SPCC) bits of the address
# and the lower logceil(SPCC) bits of the address, add them together and
# use that as a memory index.

# If SPCC gets large this will involve big muxes before and after the
# memory which will get ugly, but it feels like a good starting point.

# Actually I think we can probably barrel shift into the SPCC memories and
# then barrel shift out of them so it shouldn't be too expensive.  I think
# this only holds if logceil(SPCC) <= logceil(N)/2.

from htfft import conversions, helper


def get_mapping(N, SPCC):
    assert SPCC > 1
    assert N % SPCC == 0
    L = N // SPCC
    n_local_bits = helper.logceil(SPCC)
    mapping = {}
    for address in range(N):
        bits = conversions.int_to_str(address, helper.logceil(N))
        if n_local_bits > 0:
            lower_bits = bits[-n_local_bits:]
        else:
            lower_bits = ''
        upper_bits = bits[:n_local_bits]
        memory_index = int(lower_bits, 2) + int(upper_bits, 2)
        mapping[address] = memory_index
    all_addresses = list(range(N))
    all_reversed_addresses = [helper.reverse_bits(address, helper.logceil(N))
                              for address in all_addresses]
    for address_group in [all_addresses[index*SPCC: (index+1)*SPCC]
                          for index in range(L)]:
        assert len(set(mapping[address] for address in address_group)) == SPCC
        print(len(set(mapping[address] for address in address_group)))
    for address_group in [all_reversed_addresses[index*SPCC: (index+1)*SPCC]
                          for index in range(L)]:
        assert len(set(mapping[address] for address in address_group)) == SPCC
        print(len(set(mapping[address] for address in address_group)))
    return mapping


#def check_mapping(N, SPCC):
#    mapping = get_mapping(N, SPCC)
#    L = N // SPCC
#    memories = [[None] * L for i in range(SPCC)]
#    for address in range(N):
#        shift 


def get_memory_index(address, N, size):
    n_local_bits = helper.logceil(size)
    bits = conversions.int_to_str(address, helper.logceil(N))
    if n_local_bits > 0:
        lower_bits = bits[-n_local_bits:]
    else:
        lower_bits = ''
    upper_bits = ''.join(reversed(bits[:n_local_bits]))
    memory_index = (int(lower_bits, 2) + int(upper_bits, 2)) % size
    return memory_index


def test_initial_memory(N, size):
    L = N//size
    memories = [[None]*L for i in range(size)]
    data = list(range(N))
    for address, value in enumerate(data):
        reversed_address = helper.reverse_bits(address, helper.logceil(N))
        memory_index = get_memory_index(address, N, size)
        print(address, reversed_address)
        assert memory_index == get_memory_index(reversed_address, N, size)
        memories[memory_index][address//size] = value
    print(memories)
    for address, value in enumerate(data):
        memory_index = get_memory_index(address, N, size)
        reversed_address = helper.reverse_bits(address, helper.logceil(N))
        assert reversed_address in memories[memory_index]
        location = memories[memory_index].index(reversed_address)
        expected_location = 
        print(address, memory_index, location)

if __name__ == '__main__':
    test_initial_memory(32, 4)
